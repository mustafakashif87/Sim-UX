"""Evaluation metrics over runs.csv rows (spec: Evaluation protocol, Metrics).

Pure functions, no browser or model, so they are unit-tested on a synthetic
runs.csv. `agent/evaluate.py` writes the rows; this module scores them.

Every number is over all runs, never the best run. A bug's detection rate is
k/n per condition; it is stable at STABLE_SHARE of runs or more (4/5).
Attribution: stable in Persona on buggy, and not stable in Baseline on buggy
or in Persona on clean.

Trigger rate and detection given trigger (decision OD-3): the 4-of-5 rule
measures how often a mistake is injected as much as how the page handles it,
so each bug's runs are also split by whether the mistake its signal needs
happened (TRIGGERS). Signals with no entry need no injected mistake.
"""

import csv
from collections import defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path

STABLE_SHARE = 0.8
CONDITIONS = ("persona_buggy", "baseline_buggy", "persona_clean")
EXCLUDED = {"aborted_provider", "crashed"}  # not evidence about the page; rerun

# Perturbations a signal needs before the page can show it.
TRIGGERS = {
    "data_loss_on_error": {"typo", "skip_field"},
    "error_not_identified": {"typo", "skip_field"},
    "error_not_actionable": {"typo", "skip_field"},
    "duplicate_submission": {"double_submit"},
    "no_way_back": {"back_press"},
}

FIELDS = [
    "run_id",
    "persona",
    "bug",
    "page",
    "condition",
    "seed",
    "status",
    "steps",
    "seconds",
    "signals",
    "expected_signal",
    "detected",
    "perturbations",
    "quotes_generated",
    "quotes_verified",
    "model_id",
    "log_dir",
    "error",
]


def read_runs(path: Path) -> list[dict]:
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _split(value: str) -> list[str]:
    return [v for v in (value or "").split(";") if v]


def _counted(rows: list[dict]) -> list[dict]:
    return [r for r in rows if r["status"] not in EXCLUDED]


@dataclass(frozen=True)
class BugResult:
    bug: str
    signal: str
    rates: dict[str, tuple[int, int]]  # condition -> (k, n)
    triggered: tuple[int, int]  # persona_buggy runs where the trigger happened: (k, n)
    detected_given_trigger: tuple[int, int]
    stable: bool
    attributed: bool


def stable(k: int, n: int) -> bool:
    return n > 0 and k / n >= STABLE_SHARE


def per_bug(rows: list[dict]) -> list[BugResult]:
    by_bug: dict[str, list[dict]] = defaultdict(list)
    for r in _counted(rows):
        by_bug[r["bug"]].append(r)
    out = []
    for bug in sorted(by_bug, key=_bug_order):
        runs = by_bug[bug]
        signal = runs[0]["expected_signal"]
        rates = {}
        for cond in CONDITIONS:
            sub = [r for r in runs if r["condition"] == cond]
            rates[cond] = (sum(signal in _split(r["signals"]) for r in sub), len(sub))
        buggy = [r for r in runs if r["condition"] == "persona_buggy"]
        needs = TRIGGERS.get(signal)
        hit = [r for r in buggy if needs is None or needs & set(_split(r["perturbations"]))]
        given = (sum(signal in _split(r["signals"]) for r in hit), len(hit))
        is_stable = stable(*rates["persona_buggy"])
        attributed = (
            is_stable
            and not stable(*rates["baseline_buggy"])
            and not stable(*rates["persona_clean"])
        )
        out.append(
            BugResult(bug, signal, rates, (len(hit), len(buggy)), given, is_stable, attributed)
        )
    return out


def _bug_order(bug: str) -> tuple:
    head = bug.rstrip("0123456789")
    return (head, int(bug[len(head) :] or 0))


@dataclass(frozen=True)
class Summary:
    runs: int
    excluded: int
    recall: float | None
    precision: float | None
    false_positive_rate: float | None
    citation_validity: float | None
    mean_steps: float | None
    mean_seconds: float | None
    stable_bugs: int
    attributed_bugs: int
    bugs: int


def summarise(rows: list[dict]) -> Summary:
    counted = _counted(rows)
    bugs = per_bug(rows)
    persona_runs = [r for r in counted if r["condition"] != "baseline_buggy"]
    findings = correct = 0
    for r in persona_runs:
        signals = _split(r["signals"])
        findings += len(signals)
        if r["condition"] == "persona_buggy":
            correct += signals.count(r["expected_signal"])
    clean = [r for r in counted if r["condition"] == "persona_clean"]
    clean_findings = sum(len(_split(r["signals"])) for r in clean)
    generated = sum(int(r["quotes_generated"] or 0) for r in counted)
    verified = sum(int(r["quotes_verified"] or 0) for r in counted)
    return Summary(
        runs=len(rows),
        excluded=len(rows) - len(counted),
        recall=_ratio(sum(b.attributed for b in bugs), len(bugs)),
        precision=_ratio(correct, findings),
        false_positive_rate=_ratio(clean_findings, len(clean)),
        citation_validity=_ratio(verified, generated),
        mean_steps=_mean([float(r["steps"]) for r in counted]),
        mean_seconds=_mean([float(r["seconds"]) for r in counted]),
        stable_bugs=sum(b.stable for b in bugs),
        attributed_bugs=sum(b.attributed for b in bugs),
        bugs=len(bugs),
    )


def _ratio(a: int, b: int) -> float | None:
    return round(a / b, 3) if b else None


def _mean(values: list[float]) -> float | None:
    return round(sum(values) / len(values), 2) if values else None


def _kn(pair: tuple[int, int]) -> str:
    return f"{pair[0]}/{pair[1]}"


def markdown(rows: list[dict]) -> str:
    """The results as the report shows them: one row per bug, then totals."""
    s = summarise(rows)
    lines = [
        "| Bug | Signal | Persona on buggy | Baseline on buggy | Persona on clean "
        "| Triggered | Detected given trigger | Stable | Attributed |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for b in per_bug(rows):
        lines.append(
            f"| {b.bug} | `{b.signal}` | {_kn(b.rates['persona_buggy'])} "
            f"| {_kn(b.rates['baseline_buggy'])} | {_kn(b.rates['persona_clean'])} "
            f"| {_kn(b.triggered)} | {_kn(b.detected_given_trigger)} "
            f"| {'yes' if b.stable else 'no'} | {'yes' if b.attributed else 'no'} |"
        )

    def fmt(v):
        return "n/a" if v is None else f"{v}"

    lines += [
        "",
        f"- Runs: {s.runs} ({s.excluded} excluded: provider or harness failure)",
        f"- Recall (attributed / bugs): {fmt(s.recall)} ({s.attributed_bugs}/{s.bugs})",
        f"- Precision (expected signal / all persona findings): {fmt(s.precision)}",
        f"- False-positive rate (findings / clean runs): {fmt(s.false_positive_rate)}",
        f"- Citation validity (verified / generated quotes): {fmt(s.citation_validity)}",
        f"- Mean steps per run: {fmt(s.mean_steps)}; mean seconds: {fmt(s.mean_seconds)}",
    ]
    return "\n".join(lines) + "\n"


def as_json(rows: list[dict]) -> dict:
    return {
        "summary": asdict(summarise(rows)),
        "bugs": [asdict(b) for b in per_bug(rows)],
    }
