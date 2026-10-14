"""The mid-eval demo in one command: P1 on four pages, live or from the recording.

    python -m agent.demo                      # live: real model, browser visible
    python -m agent.demo --replay             # fallback: recorded replies, no network
    python -m agent.demo --replay --from signup-a   # continue after a live failure
    python -m agent.demo --check              # before the panel: key and recordings
    python -m agent.demo --record             # live, saved as the new recording

Runs each buggy/clean pair with the seed that makes P1's slip happen at the
configured rates (docs/demo-script.md), pausing for Enter between pages, then
prints one summary table. Live runs give up fast (2 attempts, 20 s a call):
on a failure the demo stops and prints the command to continue with. It never
switches to the recording by itself, so a replay is always announced.

A live run saves its replies to `live-cache/`, never over the recording in
`llm-cache/`: at temperature 0 a rehearsal can still answer differently, and
overwriting one recorded reply breaks the replay from that step on. Only
`--record` replaces the recording, on purpose.
"""

import argparse
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import sync_playwright

from agent.contracts import Finding, Observation
from agent.llm import LLMClient, ProviderError
from agent.loop import RunResult
from agent.run import execute, report

LOGS = Path("logs/demo")
RECORDING = "llm-cache"  # what --replay reads; written only by --record
LIVE_CACHE = "live-cache"  # what a live run writes; git-ignored


@dataclass(frozen=True)
class DemoRun:
    page: str
    seed: int
    expected: str | None  # the finding the ground truth predicts; None on a clean page


DEMO = [
    DemoRun("order-a", 1, "duplicate_submission"),  # seed 1 doubles the first click
    DemoRun("order-b", 1, None),
    DemoRun("signup-a", 69, "data_loss_on_error"),  # seed 69 skips the email field
    DemoRun("signup-b", 69, None),
]

# The visible browser is full Chromium; CI and the setup docs install only the
# headless shell, which --headless (and every test) uses.
INSTALL_BROWSER = "playwright install chromium"


def _missing_browser(error: Exception) -> bool:
    return "Executable doesn't exist" in str(error)


# Live demo limits: fail fast and say so, instead of waiting on a rate limit.
DEMO_LIMITS = {"max_attempts": 2, "max_wait_s": 10.0, "timeout_s": 20.0}


def make_model(replay: bool, logs: Path = LOGS, record: bool = False) -> LLMClient:
    cache = RECORDING if replay or record else LIVE_CACHE
    return LLMClient.from_env(cache_dir=logs / cache, replay=replay, **DEMO_LIMITS)


def _banner(text: str) -> str:
    line = "=" * max(60, len(text) + 4)
    return f"{line}\n  {text}\n{line}"


def _mode(replay: bool) -> str:
    return "REPLAY of recorded model replies (not live)" if replay else "LIVE"


def _signals(findings: list[Finding]) -> str:
    return ", ".join(f.signal for f in findings) or "none"


def summary(rows: list[tuple[DemoRun, str, RunResult, list[Finding]]]) -> str:
    lines = ["", f"{'page':<10}{'seed':<6}{'mode':<8}{'status':<18}{'finding':<24}expected"]
    for demo, mode, result, findings in rows:
        got = {f.signal for f in findings}
        want = {demo.expected} if demo.expected else set()
        mark = "as expected" if got == want else f"EXPECTED {demo.expected or 'none'}"
        lines.append(
            f"{demo.page:<10}{demo.seed:<6}{mode:<8}{result.status:<18}"
            f"{_signals(findings):<24}{mark}"
        )
    return "\n".join(lines)


def _next_command(page: str, failed_live: bool) -> str:
    if failed_live:
        return f"python -m agent.demo --replay --from {page}"
    return "pytest -v tests/e2e/test_test_app.py --override-ini addopts=   (scripted model)"


def demo(
    replay: bool,
    start: str | None,
    pause: bool,
    headed: bool,
    logs: Path = LOGS,
    record: bool = False,
) -> int:
    names = [d.page for d in DEMO]
    if start is not None and start not in names:
        print(f"--from must be one of: {', '.join(names)}", file=sys.stderr)
        return 2
    runs = DEMO[names.index(start) :] if start else DEMO
    mode = "REPLAY" if replay else "LIVE"

    try:
        model = make_model(replay, logs, record)
    except ValueError as e:  # no key, unknown provider
        print(f"Cannot start the live demo: {e}")
        print(f"Continue with: {_next_command(runs[0].page, not replay)}")
        return 1
    print(_banner(f"SimUX demo: P1 Error-prone user, {_mode(replay)}, model {model.model_id}"))

    rows = []
    for i, d in enumerate(runs):
        print(f"\n--- {d.page} (seed {d.seed}) [{mode}] ---")
        try:
            result, findings = execute(d.page, d.seed, model, logs, headed=headed)
        except Exception as e:  # a crash must not end the demo without a way on
            if _missing_browser(e):  # not the model's fault: the replay would fail too
                print(_banner("The browser is not installed; the model was not reached."))
                print(f"Run: {INSTALL_BROWSER}   then the same command again")
                print("(or add --headless to run without a visible browser)")
                return 1
            print(report_failure(d.page, f"crashed: {e}", replay, rows))
            return 1
        print(report(result, findings))
        if result.status in ("aborted_provider", "crashed"):
            print(report_failure(d.page, result.meta.get("error", result.status), replay, rows))
            return 1
        rows.append((d, mode, result, findings))
        if pause and i < len(runs) - 1:
            input("\nPress Enter for the next page... ")

    print(summary(rows))
    return 0


def report_failure(page: str, reason: str, replay: bool, rows: list) -> str:
    what = "REPLAY" if replay else "LIVE"
    short = str(reason).strip().splitlines()[0][:90]  # providers append raw JSON
    lines = [
        "",
        _banner(f"{what} RUN FAILED on {page}: {short}"),
        f"Continue with: {_next_command(page, not replay)}",
    ]
    if rows:
        lines.append(summary(rows))
    return "\n".join(lines)


def check(logs: Path = LOGS) -> int:
    """Before the panel arrives: the visible browser opens, one live call
    answers, and every recorded run replays headless into a temporary folder,
    so logs/demo is left as it is."""
    ok = True
    try:
        with sync_playwright() as pw:
            pw.chromium.launch(headless=False).close()
        print("OK    visible browser opens")
    except PlaywrightError as e:
        ok = False
        hint = f"run: {INSTALL_BROWSER}" if _missing_browser(e) else str(e).splitlines()[0]
        print(f"FAIL  visible browser: {hint}")
    try:
        model = LLMClient.from_env(**DEMO_LIMITS)  # records nothing into logs/demo
        obs = Observation(step=0, tree='- button "Send" [ref=e1]', url_path="/check.html")
        action = model.next_action("Press the Send button.", obs, [])
        print(f"OK    live model {model.model_id} answered: {action.action} {action.ref or ''}")
    except (ValueError, ProviderError) as e:
        ok = False
        print(f"FAIL  live model: {e}")

    replayed = make_model(True, logs)
    with tempfile.TemporaryDirectory() as tmp:
        for d in DEMO:
            try:
                result, findings = execute(d.page, d.seed, replayed, Path(tmp))
            except Exception as e:
                ok = False
                hint = f"run: {INSTALL_BROWSER}" if _missing_browser(e) else str(e)
                print(f"FAIL  replay {d.page:<9} seed {d.seed:<3} {hint.splitlines()[0]}")
                continue
            want = {d.expected} if d.expected else set()
            good = result.status == "succeeded" and {f.signal for f in findings} == want
            ok &= good
            print(
                f"{'OK  ' if good else 'FAIL'}  replay {d.page:<9} seed {d.seed:<3} "
                f"{result.status:<17} findings: {_signals(findings)}"
            )
    print("\nReady." if ok else "\nNot ready: fix the FAIL lines above.")
    return 0 if ok else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m agent.demo", description=__doc__.split("\n")[0]
    )
    parser.add_argument("--replay", action="store_true", help="recorded replies, no network")
    parser.add_argument("--from", dest="start", metavar="PAGE", help="start at this page")
    parser.add_argument("--record", action="store_true", help="live, saved as the recording")
    parser.add_argument("--check", action="store_true", help="check key and recordings, then exit")
    parser.add_argument("--no-pause", action="store_true", help="do not wait for Enter")
    parser.add_argument("--headless", action="store_true", help="hide the browser")
    parser.add_argument("--logs", type=Path, default=LOGS, help="log root holding llm-cache/")
    args = parser.parse_args(argv)
    if args.record and args.replay:
        parser.error("--record is a live run; it cannot be combined with --replay")
    if args.check:
        return check(args.logs)
    pause, headed = not args.no_pause, not args.headless
    return demo(args.replay, args.start, pause, headed, args.logs, args.record)


if __name__ == "__main__":
    sys.exit(main())
