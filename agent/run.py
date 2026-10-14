"""Run one persona on one test-app page with the real model, from the command line.

    python -m agent.run --page signup-a --seed 69
    python -m agent.run --page order-a --seed 1 --logs logs/demo --replay

Serves `test-app/` locally (or uses `--base`, e.g. the GitHub Pages site),
runs the loop with the LLM client from `.env` or the environment, then prints
each step's intended and executed action and the findings the detectors read
from the log. Logs go to `<logs>/<run_id>/`; model replies are recorded in
`<logs>/llm-cache/`, which `--replay` serves with no API call.
"""

import argparse
import sys
from contextlib import nullcontext
from pathlib import Path

from playwright.sync_api import Browser, sync_playwright

from agent.contracts import Action, Finding
from agent.detectors import detect, load_run
from agent.llm import LLMClient
from agent.loop import Model, RunResult, run
from agent.persona import load_persona
from agent.tasks import load_tasks, serve

# Slows each browser action in --headed mode so the audience can follow it.
HEADED_SLOW_MO_MS = 300


def execute(
    page_name: str,
    seed: int | None,
    model: Model,
    logs: Path,
    persona: str = "error_prone",
    base: str | None = None,
    headed: bool = False,
    browser: Browser | None = None,
) -> tuple[RunResult, list[Finding]]:
    """One run of `persona` on `<page_name>.html`, and the findings from its log.
    Launches Chromium unless given a `browser` (tests share one)."""
    with serve() if base is None else nullcontext(base) as url:
        tasks = {t.url.rsplit("/", 1)[-1]: t for t in load_tasks(url)}
        task = tasks.get(f"{page_name}.html")
        if task is None:
            names = sorted(name.removesuffix(".html") for name in tasks)
            raise SystemExit(f"no task for page {page_name!r}; pages: {', '.join(names)}")
        p = load_persona(persona)
        if browser is not None:
            result = _run_in(browser, task, p, model, logs, seed)
        else:
            with sync_playwright() as pw:
                slow_mo = HEADED_SLOW_MO_MS if headed else 0
                launched = pw.chromium.launch(headless=not headed, slow_mo=slow_mo)
                try:
                    result = _run_in(launched, task, p, model, logs, seed)
                finally:
                    launched.close()
    return result, detect(load_run(result.log_dir))


def _run_in(browser: Browser, task, persona, model, logs, seed) -> RunResult:
    page = browser.new_page()
    try:
        return run(page, task, persona, model, logs, seed)
    finally:
        page.close()


def _describe(action: Action | None) -> str:
    if action is None:
        return "(nothing)"
    target = action.ref or action.key or ""
    text = f" {action.text!r}" if action.text is not None else ""
    return f"{action.action} {target}{text}".strip()


def report(result: RunResult, findings: list[Finding]) -> str:
    meta = result.meta
    lines = [
        f"run {result.run_id}: {meta['persona']} on {meta['page']}, seed {meta['seed']}, "
        f"model {meta['model_id']}",
        *(["REPLAY of recorded model replies, not a live run"] if meta.get("replay") else []),
        "",
        f"{'step':<5}{'intended':<38}{'executed':<38}{'mistake':<15}{'result':<8}goal",
    ]
    for s in result.steps:
        lines.append(
            f"{s.step:<5}{_describe(s.intended_action):<38}{_describe(s.executed_action):<38}"
            f"{s.perturbation or '-':<15}{s.result:<8}{'yes' if s.goal_reached else ''}"
        )
    lines += ["", f"status: {result.status} after {len(result.steps)} steps"]
    if meta.get("error"):
        lines.append(f"error: {meta['error']}")
    lines.append(f"log: {result.log_dir}")
    lines.append("")
    if not findings:
        lines.append("findings: none")
    for f in findings:
        lines.append(
            f"finding: {f.signal}, severity {f.severity}, "
            f"{' / '.join(f.candidate_criteria)}, evidence steps {f.evidence_steps}"
        )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m agent.run", description=__doc__.split("\n")[0])
    parser.add_argument("--page", required=True, help="test-app page without .html, e.g. order-a")
    parser.add_argument(
        "--seed", type=int, default=None, help="perturbation seed (default: config)"
    )
    parser.add_argument("--persona", default="error_prone")
    parser.add_argument("--logs", type=Path, default=Path("logs/runs"), help="log root")
    parser.add_argument("--base", help="serve pages from this URL instead of test-app/")
    parser.add_argument("--replay", action="store_true", help="recorded replies only, no API call")
    parser.add_argument("--headed", action="store_true", help="show the browser, slowed down")
    args = parser.parse_args(argv)

    model = LLMClient.from_env(cache_dir=args.logs / "llm-cache", replay=args.replay)
    result, findings = execute(
        args.page, args.seed, model, args.logs, args.persona, args.base, args.headed
    )
    print(report(result, findings))
    return 1 if result.status in ("aborted_provider", "crashed") else 0


if __name__ == "__main__":
    sys.exit(main())
