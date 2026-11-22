"""The comparison table: one row per seeded bug, one column per system
(spec: Evaluation protocol, Comparison systems; proposal feature 10).

Columns:
- SimUX persona: k/n in Persona on buggy from each persona's runs.csv, and
  whether the attribution rule holds.
- Keyboard sweep: `agent.keyboard_sweep` on the buggy and the clean page.
- axe-core: rules that fire on the buggy page and not on the clean one.
- Single-prompt LLM: the model sees the page's first accessibility tree and
  the task once, and lists problems, each tagged with one signal from the
  signal map. Detected when the bug's signal is listed for the buggy page
  and not for the clean one. It cannot act, so it never sees behaviour.

A bug counts as detected by a system only if the buggy page differs from the
clean one, so a system that reports everything everywhere scores nothing.

    python -m agent.compare --runs eval-out/p1 eval-out/p2 --axe-js axe.min.js --out compare
    python -m agent.compare --runs eval-out/p1 --axe-summary axe-results/summary.json --no-llm
"""

import argparse
import json
import sys
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

from agent import metrics
from agent.tasks import SeededBug, load_seeded_bugs, load_tasks, serve

SINGLE_PROMPT = """\
You review a web page for usability and accessibility problems that would \
stop or slow a person doing the task below. You see the page once, as an \
accessibility tree.

List every problem you find. Tag each with exactly one signal from this \
list, or "other":
{signals}

Reply with one JSON object and nothing else:
{{"problems": [{{"signal": "<signal or other>", "evidence": "<short quote from the tree>"}}]}}"""

# One line each, so the single-prompt baseline knows what a signal means.
SIGNAL_HINTS = {
    "data_loss_on_error": "an error on submit clears values the user had entered",
    "error_not_identified": "invalid input is rejected without saying what is wrong",
    "error_not_actionable": "an error message does not name the field or the fix",
    "duplicate_submission": "a submit button can send the same request twice",
    "destructive_without_confirm": "a destructive action happens with no confirmation",
    "no_way_back": "the user cannot go back to a previous step without losing work",
    "redundant_entry": "the user must type information again that was already given",
    "recall_required": "information from an earlier step must be remembered",
    "lost_location": "nothing tells the user where they are in a flow",
    "no_progress_indicator": "a multi-step flow has no step number or progress",
    "label_unintelligible": "a label or button uses words a plain reader would not know",
    "instruction_unintelligible": "an instruction is written in jargon",
    "system_language": "a message uses internal codes instead of plain words",
    "image-alt": "an image has no text alternative",
    "button-name": "a button has no accessible name",
    "label": "a form field has no label",
    "keyboard_trap": "keyboard focus gets stuck",
    "unreachable_control": "a control cannot be reached with the keyboard",
}

# SEEDED_BUGS.md names the keyboard bugs in words; their sweep signals.
_ALIASES = {"Tab-cycle trap": "keyboard_trap", "unreachable control": "unreachable_control"}


def signal_of(bug: SeededBug) -> str | None:
    return _ALIASES.get(bug.signal, bug.signal) if bug.signal else None


SYSTEMS = ("simux", "keyboard_sweep", "axe", "single_prompt")


@dataclass
class Row:
    bug: SeededBug
    cells: dict[str, str] = field(default_factory=dict)
    detected: dict[str, bool] = field(default_factory=dict)


def simux_cells(rows_by_bug: dict[str, metrics.BugResult], bug: SeededBug) -> tuple[str, bool]:
    result = rows_by_bug.get(bug.id)
    if result is None:
        return "not run", False
    k, n = result.rates["persona_buggy"]
    note = "attributed" if result.attributed else ("stable" if result.stable else "unstable")
    return f"{k}/{n} ({note})", result.attributed


def differs(buggy: set[str], clean: set[str]) -> set[str]:
    return buggy - clean


def single_prompt_signals(complete: Callable[[list[dict]], str], task: str, tree: str) -> set[str]:
    signals = "\n".join(f"- {s}: {hint}" for s, hint in SIGNAL_HINTS.items())
    messages = [
        {"role": "system", "content": SINGLE_PROMPT.format(signals=signals)},
        {"role": "user", "content": f"Task: {task}\n\nAccessibility tree:\n{tree}"},
    ]
    try:
        reply = json.loads(complete(messages))
        return {
            p["signal"]
            for p in reply.get("problems", [])
            if isinstance(p, dict) and p.get("signal") in SIGNAL_HINTS
        }
    except (ValueError, AttributeError, TypeError):
        return set()


def build(
    runs_dirs: list[Path],
    axe: dict[str, set[str]] | None,
    sweep: dict[str, set[str]] | None,
    single: dict[str, set[str]] | None,
) -> list[Row]:
    results: dict[str, metrics.BugResult] = {}
    for d in runs_dirs:
        for r in metrics.per_bug(metrics.read_runs(d / "runs.csv")):
            results[r.bug] = r
    out = []
    for bug in load_seeded_bugs():
        row = Row(bug)
        row.cells["simux"], row.detected["simux"] = simux_cells(results, bug)
        for name, found in (("keyboard_sweep", sweep), ("axe", axe), ("single_prompt", single)):
            if found is None:
                row.cells[name], row.detected[name] = "not run", False
                continue
            extra = differs(found.get(bug.buggy, set()), found.get(bug.clean, set()))
            if name == "single_prompt":  # must name the right signal
                hit = signal_of(bug) in extra
            else:  # any rule that fires only on the buggy page
                hit = bool(extra)
            row.cells[name] = ("yes: " if hit else "no" + (": " if extra else "")) + ", ".join(
                sorted(extra)
            )
            row.detected[name] = hit
        out.append(row)
    return out


def markdown(rows: list[Row]) -> str:
    lines = [
        "| Bug | Expected signal | SimUX persona | Keyboard sweep | axe-core | Single-prompt LLM |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for r in rows:
        cells = [r.cells[s] for s in SYSTEMS]
        lines.append(f"| {r.bug.id} | `{signal_of(r.bug) or 'none'}` | " + " | ".join(cells) + " |")
    totals = [sum(r.detected[s] for r in rows) for s in SYSTEMS]
    lines.append(f"| **Detected** | | {' | '.join(f'{t}/{len(rows)}' for t in totals)} |")
    return "\n".join(lines) + "\n"


# --- live checks: axe, keyboard sweep, single prompt -------------------------


def run_live(
    axe_js: Path | None, do_sweep: bool, complete: Callable | None
) -> tuple[dict | None, dict | None, dict | None]:
    from playwright.sync_api import sync_playwright

    from agent.browser import observe, settle
    from agent.keyboard_sweep import sweep

    pages = sorted({p for b in load_seeded_bugs() for p in (b.buggy, b.clean)})
    axe: dict[str, set[str]] | None = {} if axe_js else None
    swept: dict[str, set[str]] | None = {} if do_sweep else None
    single: dict[str, set[str]] | None = {} if complete else None
    with serve() as base, sync_playwright() as p:
        tasks = {t.url.rsplit("/", 1)[-1]: t.text for t in load_tasks(base)}
        browser = p.chromium.launch()
        for name in pages:
            page = browser.new_page()
            page.goto(base + name)
            settle(page)
            if single is not None:
                obs, _ = observe(page, 0, ["full_tree"])
                task = tasks.get(name, "Use this page as a shopper would.")
                single[name] = single_prompt_signals(complete, task, obs.tree)
            if axe is not None:
                page.add_script_tag(path=str(axe_js))
                result = page.evaluate("() => window.axe.run()")
                axe[name] = {v["id"] for v in result["violations"]}
            if swept is not None:
                swept[name] = {i.signal for i in sweep(page)}
            page.close()
        browser.close()
    return axe, swept, single


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m agent.compare", description=__doc__.split("\n")[0]
    )
    parser.add_argument("--runs", type=Path, nargs="*", default=[], help="evaluate --out folders")
    parser.add_argument("--axe-js", type=Path, help="axe.min.js, to run axe here")
    parser.add_argument("--axe-summary", type=Path, help="summary.json from CI's axe job")
    parser.add_argument("--no-sweep", action="store_true")
    parser.add_argument("--no-llm", action="store_true", help="skip the single-prompt baseline")
    parser.add_argument("--replay", action="store_true", help="recorded LLM replies only")
    parser.add_argument("--out", type=Path, default=Path("compare-out"))
    args = parser.parse_args(argv)

    args.out.mkdir(parents=True, exist_ok=True)
    complete = None
    if not args.no_llm:
        from agent.llm import LLMClient

        client = LLMClient.from_env(cache_dir=args.out / "llm-cache", replay=args.replay)
        complete = client.complete
    axe, swept, single = run_live(args.axe_js, not args.no_sweep, complete)
    if axe is None and args.axe_summary:
        raw = json.loads(args.axe_summary.read_text(encoding="utf-8"))
        axe = {page: {v["id"] for v in found} for page, found in raw.items()}
    rows = build(args.runs, axe, swept, single)
    table = markdown(rows)
    (args.out / "comparison.md").write_text(table, encoding="utf-8")
    raw = {"axe": axe, "keyboard_sweep": swept, "single_prompt": single}
    (args.out / "raw.json").write_text(
        json.dumps(
            {k: v and {p: sorted(s) for p, s in v.items()} for k, v in raw.items()}, indent=1
        ),
        encoding="utf-8",
    )
    print(table)
    return 0


if __name__ == "__main__":
    sys.exit(main())
