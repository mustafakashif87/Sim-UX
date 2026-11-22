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
from functools import cache
from pathlib import Path

from agent.contracts import Finding, Observation, StepRecord
from grounding.ground import SignalMap, default_signal_map, severity, start_confidence


@cache
def signal_map() -> SignalMap:
    """grounding/signal_map.yaml: the single source of truth for each signal's
    candidate criteria and type (spec: Grounding pipeline, step 2)."""
    return default_signal_map()


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


def make_finding(
    run: RunLog, signal: str, evidence_steps: list[int], *, data_loss: bool = False
) -> Finding:
    """A Finding whose candidates, severity and starting confidence all come
    from grounding/, so detectors and grounding cannot disagree.

    Severity is the spec's rule (grounding.severity): 4 if the task was not
    completed, 3 if completed with data loss, otherwise 2.
    """
    entry = signal_map().entry(signal)
    return Finding(
        finding_id=f"{run.meta['run_id']}-{signal}",
        persona=run.meta["persona"],
        page=run.meta["page"],
        signal=signal,
        evidence_steps=evidence_steps,
        candidate_criteria=signal_map().candidates(signal),
        severity=severity(task_completed=run.meta["status"] == "succeeded", data_loss=data_loss),
        # Times the k/5 reproduction rate once runs are repeated.
        confidence=start_confidence(entry.type),
        # Unknown until the baseline condition runs on the same page.
        baseline_reproduced=False,
    )


Detector = Callable[[RunLog], Finding | None]


def detect(run: RunLog) -> list[Finding]:
    """Run every P1 detector on one run. An aborted run yields none: it ended
    because the model could not answer, so it says nothing about the page."""
    if run.meta.get("status") == "aborted_provider":
        return []
    from agent.detectors.data_loss import data_loss_on_error
    from agent.detectors.destructive import destructive_without_confirm
    from agent.detectors.duplicate_submission import duplicate_submission
    from agent.detectors.error_not_identified import error_not_identified
    from agent.detectors.no_way_back import no_way_back
    from agent.detectors.redundant_entry import redundant_entry

    detectors: list[Detector] = [
        data_loss_on_error,
        error_not_identified,
        duplicate_submission,
        destructive_without_confirm,
        no_way_back,
        redundant_entry,
    ]
    return [f for d in detectors if (f := d(run)) is not None]


def audit(log_dir: Path) -> list[Finding]:
    """A finished run's findings, each with its verified citations or marked
    ungrounded (no citations, lower confidence). What `agent.run` prints and
    the API returns."""
    from grounding.ground import ground_all

    return [r.finding for r in ground_all(detect(load_run(log_dir)))]
