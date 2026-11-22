"""Run the evaluation protocol for one persona (spec: Evaluation protocol).

    python -m agent.evaluate --persona error_prone --seeds 5 --out eval-out
    python -m agent.evaluate --persona error_prone --seeds 1 --bugs B4,B5 --out eval-out

Every seeded bug whose expected signal belongs to the persona (its `source`
in grounding/signal_map.yaml) is run under three conditions, once per seed
1..N:

| Condition       | Persona            | Page  |
| --------------- | ------------------ | ----- |
| persona_buggy   | as configured      | buggy |
| baseline_buggy  | every limit off    | buggy |
| persona_clean   | as configured      | clean |

Writes under --out: one log folder per run in `runs/`, `runs.csv` (one row
per run, see agent.metrics.FIELDS), and from it `summary.md` and
`metrics.json`. Model replies are recorded in `llm-cache/`.

`--rescore` runs no model: it re-reads every logged run with the current
detectors and rewrites runs.csv, summary.md and metrics.json. Detectors only
read logs, so a detector built after the runs is scored on the same runs.

Resumable: rows already in runs.csv are kept and not rerun, except runs the
provider or harness ended (`aborted_provider`, `crashed`), which say nothing
about the page. When the provider reports a spent quota the evaluation stops
there; run the same command again later to continue.
"""

import argparse
import csv
import json
import sys
import time
from collections.abc import Callable, Iterator
from contextlib import nullcontext
from dataclasses import dataclass
from pathlib import Path

from agent import metrics
from agent.detectors import detect, load_run
from agent.loop import Model, run
from agent.persona import for_condition, load_persona
from agent.tasks import SeededBug, load_seeded_bugs, load_tasks, serve
from grounding.ground import default_signal_map, ground_all

CONDITIONS = {
    "persona_buggy": ("persona", "buggy"),
    "baseline_buggy": ("baseline", "buggy"),
    "persona_clean": ("persona", "clean"),
}


@dataclass(frozen=True)
class Job:
    bug: SeededBug
    condition: str
    seed: int

    @property
    def page(self) -> str:
        _, version = CONDITIONS[self.condition]
        return self.bug.buggy if version == "buggy" else self.bug.clean

    @property
    def key(self) -> tuple[str, str, str]:
        return (self.bug.id, self.condition, str(self.seed))


def bugs_for(persona: str, only: list[str] | None = None) -> list[SeededBug]:
    """Seeded bugs whose expected signal this persona's detectors emit."""
    signal_map = default_signal_map()
    out = []
    for bug in load_seeded_bugs():
        if bug.signal is None or bug.signal not in signal_map:
            continue
        if signal_map.entry(bug.signal).source != persona:
            continue
        if only and bug.id not in only:
            continue
        out.append(bug)
    return out


def jobs(bugs: list[SeededBug], seeds: int, conditions: list[str]) -> Iterator[Job]:
    """Seed-major order, so a stopped evaluation has every bug at the same depth."""
    for seed in range(1, seeds + 1):
        for bug in bugs:
            for condition in conditions:
                yield Job(bug, condition, seed)


def evaluate(
    persona_id: str,
    seeds: int,
    out: Path,
    model_factory: Callable[[], Model],
    only: list[str] | None = None,
    conditions: list[str] | None = None,
    base: str | None = None,
    browser=None,
    log: Callable[[str], None] = print,
) -> list[dict]:
    """Run every missing job, append each to runs.csv as it finishes, then
    write summary.md and metrics.json. Returns all rows."""
    out.mkdir(parents=True, exist_ok=True)
    csv_path = out / "runs.csv"
    rows = metrics.read_runs(csv_path) if csv_path.exists() else []
    done = {
        (r["bug"], r["condition"], r["seed"]) for r in rows if r["status"] not in metrics.EXCLUDED
    }
    rows = [r for r in rows if (r["bug"], r["condition"], r["seed"]) in done]
    _write_all(csv_path, rows)

    bugs = bugs_for(persona_id, only)
    if not bugs:
        raise SystemExit(f"no seeded bugs with a {persona_id} signal")
    todo = [j for j in jobs(bugs, seeds, conditions or list(CONDITIONS)) if j.key not in done]
    log(f"{persona_id}: {len(bugs)} bugs, {len(done)} runs kept, {len(todo)} to run")

    persona = load_persona(persona_id)
    with serve() if base is None else nullcontext(base) as url:
        tasks = {t.url.rsplit("/", 1)[-1]: t for t in load_tasks(url)}
        with _browser(browser) as b:
            for n, job in enumerate(todo, 1):
                row = _run_job(job, tasks, persona, model_factory(), out, b)
                rows.append(row)
                _append(csv_path, row)
                log(
                    f"[{n}/{len(todo)}] {job.bug.id} {job.condition} seed {job.seed}: "
                    f"{row['status']}, {row['steps']} steps, "
                    f"signals: {row['signals'] or '-'}"
                )
                if "quota spent" in row["error"]:
                    log("Provider quota spent; stopping. Rerun the same command to continue.")
                    break

    _write_outputs(persona_id, out, rows)
    return rows


def score(row: dict, log_dir: Path) -> dict:
    """The detector columns of one row, from its run's log."""
    found = detect(load_run(log_dir))
    grounded = ground_all(found)
    signals = [f.signal for f in found]
    return {
        "signals": ";".join(signals),
        "detected": int(row["expected_signal"] in signals),
        "quotes_generated": sum(len(f.candidate_criteria) for f in found),
        "quotes_verified": sum(len(r.finding.citations) for r in grounded),
    }


def rescore(persona_id: str, out: Path) -> list[dict]:
    """Re-detect every logged run in runs.csv and rewrite the outputs."""
    rows = metrics.read_runs(out / "runs.csv")
    for row in rows:
        if row["log_dir"] and (out / row["log_dir"] / "run.json").exists():
            row |= score(row, out / row["log_dir"])
    _write_all(out / "runs.csv", rows)
    _write_outputs(persona_id, out, rows)
    return rows


def _write_outputs(persona_id: str, out: Path, rows: list[dict]) -> None:
    (out / "summary.md").write_text(_summary(persona_id, rows), encoding="utf-8")
    (out / "metrics.json").write_text(
        json.dumps(metrics.as_json(rows), indent=2) + "\n", encoding="utf-8"
    )


def _run_job(job: Job, tasks: dict, persona, model: Model, out: Path, browser) -> dict:
    condition, _ = CONDITIONS[job.condition]
    task = tasks[job.page]
    started = time.monotonic()
    row = {f: "" for f in metrics.FIELDS}
    row |= {
        "persona": persona.id,
        "bug": job.bug.id,
        "page": job.page,
        "condition": job.condition,
        "seed": job.seed,
        "expected_signal": job.bug.signal,
        "model_id": getattr(model, "model_id", ""),
    }
    page = browser.new_page()
    try:
        result = run(
            page, task, for_condition(persona, condition), model, out / "runs", job.seed, condition
        )
        row |= score(row, result.log_dir) | {
            "run_id": result.run_id,
            "status": result.status,
            "steps": len(result.steps),
            "perturbations": ";".join(s.perturbation for s in result.steps if s.perturbation),
            "log_dir": result.log_dir.relative_to(out).as_posix(),
            "error": result.meta.get("error", ""),
        }
    except Exception as e:  # noqa: BLE001 - one broken run must not end the evaluation
        row |= {"status": "crashed", "error": f"{type(e).__name__}: {e}"}
    finally:
        page.close()
    row["seconds"] = round(time.monotonic() - started, 1)
    return row


def _browser(browser):
    if browser is not None:
        return nullcontext(browser)

    from contextlib import contextmanager

    from playwright.sync_api import sync_playwright

    @contextmanager
    def launched():
        with sync_playwright() as p:
            b = p.chromium.launch()
            try:
                yield b
            finally:
                b.close()

    return launched()


def _write_all(path: Path, rows: list[dict]) -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=metrics.FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def _append(path: Path, row: dict) -> None:
    with open(path, "a", newline="", encoding="utf-8") as f:
        csv.DictWriter(f, fieldnames=metrics.FIELDS).writerow(row)


def _summary(persona_id: str, rows: list[dict]) -> str:
    models = sorted({r["model_id"] for r in rows if r["model_id"]})
    return (
        f"# Evaluation: {persona_id}\n\n"
        f"Model: {', '.join(models) or 'n/a'}. Every run is counted; k/n per condition.\n\n"
        + metrics.markdown(rows)
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m agent.evaluate", description=__doc__.split("\n")[0]
    )
    parser.add_argument("--persona", required=True)
    parser.add_argument("--seeds", type=int, default=5, help="runs per page per condition")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--bugs", help="comma-separated bug IDs, e.g. B1,B4 (default: all)")
    parser.add_argument(
        "--conditions", help=f"comma-separated, default all: {', '.join(CONDITIONS)}"
    )
    parser.add_argument("--base", help="serve pages from this URL instead of test-app/")
    parser.add_argument("--replay", action="store_true", help="recorded replies only")
    parser.add_argument("--rescore", action="store_true", help="re-detect logged runs; no model")
    args = parser.parse_args(argv)
    if args.rescore:
        print(metrics.markdown(rescore(args.persona, args.out)))
        return 0
    if not 1 <= args.seeds <= 99:
        parser.error("--seeds must be 1 to 99")
    conditions = args.conditions.split(",") if args.conditions else None
    if conditions and set(conditions) - set(CONDITIONS):
        parser.error(f"unknown condition; choose from {', '.join(CONDITIONS)}")

    from agent.llm import LLMClient

    model = LLMClient.from_env(cache_dir=args.out / "llm-cache", replay=args.replay)
    rows = evaluate(
        args.persona,
        args.seeds,
        args.out,
        lambda: model,
        only=args.bugs.split(",") if args.bugs else None,
        conditions=conditions,
        base=args.base,
    )
    print()
    print(metrics.markdown(rows))
    return 0


if __name__ == "__main__":
    sys.exit(main())
