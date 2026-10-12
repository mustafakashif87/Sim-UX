"""Detectors: read a finished run's log and emit Findings.

Detectors never see what the model said happened, only what the harness
logged (spec: Persona framework, "Detectors read the step log afterwards").
Pure Python, no browser: each is tested on hand-built logs and on buggy and
clean fixture pages.

    findings = detect(load_run(result.log_dir))
"""

import json
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from agent.contracts import Finding, Observation, StepRecord

# Candidate criteria per signal, from the spec's P1 table. Interim: once
# grounding/signal_map.yaml exists (Person C), it is the single source of
# truth and this map is read from it.
CANDIDATES = {
    "data_loss_on_error": ["Nielsen 9", "WCAG 3.3.7"],
    "duplicate_submission": ["Nielsen 5", "WCAG 3.3.4"],
}

# Spec, Grounding pipeline: deterministic signals start at 0.9 and are later
# multiplied by the reproduction rate across repeated runs.
DETERMINISTIC_CONFIDENCE = 0.9


@dataclass(frozen=True)
class Submission:
    step: int
    method: str
    url: str
    body: str | None


@dataclass(frozen=True)
class RunLog:
    """One run as the harness logged it. `observations[i]` is what the persona
    saw before step i's action; the last one is the page after the run."""

    meta: dict
    steps: list[StepRecord]
    observations: list[Observation]
    submissions: list[Submission]


def load_run(log_dir: Path) -> RunLog:
    def lines(name: str) -> list[dict]:
        path = log_dir / name
        text = path.read_text(encoding="utf-8") if path.exists() else ""
        return [json.loads(line) for line in text.splitlines() if line]

    observations = sorted(lines("observations.jsonl"), key=lambda e: e["step"])
    return RunLog(
        meta=json.loads((log_dir / "run.json").read_text(encoding="utf-8")),
        steps=[StepRecord.model_validate(e) for e in lines("steps.jsonl")],
        observations=[Observation.model_validate(e["observation"]) for e in observations],
        submissions=[Submission(**e) for e in lines("network.jsonl")],
    )


def make_finding(run: RunLog, signal: str, evidence_steps: list[int]) -> Finding:
    """A Finding with rule-based severity (spec: Grounding pipeline, Score):
    4 when the task was not completed, 3 when it was but with this harm."""
    return Finding(
        finding_id=f"{run.meta['run_id']}-{signal}",
        persona=run.meta["persona"],
        page=run.meta["page"],
        signal=signal,
        evidence_steps=evidence_steps,
        candidate_criteria=CANDIDATES[signal],
        severity=3 if run.meta["status"] == "succeeded" else 4,
        confidence=DETERMINISTIC_CONFIDENCE,
        # Unknown until the baseline condition runs on the same page.
        baseline_reproduced=False,
    )


Detector = Callable[[RunLog], Finding | None]


def detect(run: RunLog) -> list[Finding]:
    """Run every P1 detector on one run."""
    from agent.detectors.data_loss import data_loss_on_error
    from agent.detectors.duplicate_submission import duplicate_submission

    detectors: list[Detector] = [data_loss_on_error, duplicate_submission]
    return [f for d in detectors if (f := d(run)) is not None]
