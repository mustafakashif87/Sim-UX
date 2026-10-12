"""Check every seeded bug against the ground truth in SEEDED_BUGS.md.

For each row of the Bugs table, the bug must be present on the buggy page and
absent on the clean page. Exits 1 on any mismatch, or when a row has no check
here (or a check has no row), so CI's `seeds` job fails instead of trusting a
stale ground truth.

This is not the agent. Each check is a scripted user or a direct reading of
the accessibility tree, so the ground truth is verified, not assumed.

    pip install -e ".[browser]" && playwright install --only-shell chromium
    python test-app/check_seeds.py
"""

import functools
import http.server
import re
import sys
import threading
from collections.abc import Callable
from pathlib import Path

from playwright.sync_api import Browser, Page, sync_playwright

APP_DIR = Path(__file__).resolve().parent
GROUND_TRUTH = APP_DIR / "SEEDED_BUGS.md"
MAX_TABS = 25

# A check opens a fresh page and returns True when the bug is present on it.
Check = Callable[[Page], bool]
CHECKS: dict[str, Check] = {}


def check(bug_id: str):
    def register(fn: Check) -> Check:
        CHECKS[bug_id] = fn
        return fn

    return register


# --- helpers ---------------------------------------------------------------


def has_unnamed(page: Page, role: str) -> bool:
    """True when the tree has a `role` node with no accessible name."""
    tree = page.locator("body").aria_snapshot()
    return re.search(rf"^\s*- {role}(\s*\[[^\]]*\])*:?\s*$", tree, re.M) is not None


def tab_to_and_activate(page: Page, selector: str) -> bool:
    """Press Tab until `selector` has focus, then Enter. True when the
    submission lands on success.html; False when focus never gets there."""
    target = page.locator(selector)
    for _ in range(MAX_TABS):
        page.keyboard.press("Tab")
        if target.evaluate("el => el === document.activeElement"):
            page.keyboard.press("Enter")
            return reached_goal(page, "heading", "Submission received")
    return False


def reached_goal(page: Page, role: str, name: str, timeout_ms: int = 3000) -> bool:
    """The harness's goal check (agent.browser.goal_reached), with a wait."""
    try:
        page.get_by_role(role, name=name, exact=True).first.wait_for(timeout=timeout_ms)
        return True
    except Exception:
        return False


# --- SB-01 to SB-05: deterministic-layer fixtures --------------------------


@check("SB-01")
def image_without_alt(page: Page) -> bool:
    return has_unnamed(page, "img")


@check("SB-02")
def button_without_name(page: Page) -> bool:
    return has_unnamed(page, "button")


@check("SB-03")
def field_without_label(page: Page) -> bool:
    return has_unnamed(page, "textbox")


@check("SB-04")
def focus_trap(page: Page) -> bool:
    return not tab_to_and_activate(page, "button[type=submit]")


@check("SB-05")
def mouse_only_control(page: Page) -> bool:
    return not tab_to_and_activate(page, "#confirm")


# --- runner ----------------------------------------------------------------


def ground_truth() -> list[tuple[str, str, str]]:
    """(id, buggy page, clean page) for each row of the Bugs table."""
    rows = []
    for line in GROUND_TRUTH.read_text(encoding="utf-8").splitlines():
        cells = [c.strip().strip("`") for c in line.strip().strip("|").split("|")]
        if len(cells) >= 3 and re.fullmatch(r"(SB-\d+|B\d+)", cells[0]):
            rows.append((cells[0], cells[1], cells[2]))
    return rows


class _QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


def _serve() -> http.server.ThreadingHTTPServer:
    handler = functools.partial(_QuietHandler, directory=str(APP_DIR))
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server


def _present(browser: Browser, base: str, name: str, fn: Check) -> bool:
    page = browser.new_page()
    try:
        page.goto(f"{base}/{name}")
        return fn(page)
    finally:
        page.close()


def main() -> int:
    rows = ground_truth()
    problems = [
        f"{bug}: in SEEDED_BUGS.md but has no check" for bug, *_ in rows if bug not in CHECKS
    ]
    problems += [
        f"{bug}: has a check but no row in SEEDED_BUGS.md"
        for bug in CHECKS
        if bug not in {r[0] for r in rows}
    ]

    server = _serve()
    base = f"http://127.0.0.1:{server.server_port}"
    print(f"{'bug':<6} {'buggy page':<20} {'present':<8} {'clean page':<20} present")
    with sync_playwright() as p:
        browser = p.chromium.launch()
        for bug, buggy, clean in rows:
            if bug not in CHECKS:
                continue
            on_buggy = _present(browser, base, buggy, CHECKS[bug])
            on_clean = _present(browser, base, clean, CHECKS[bug])
            print(f"{bug:<6} {buggy:<20} {on_buggy!s:<8} {clean:<20} {on_clean}")
            if not on_buggy:
                problems.append(f"{bug}: missing from buggy page {buggy}")
            if on_clean:
                problems.append(f"{bug}: present on clean page {clean}")
        browser.close()
    server.shutdown()

    for problem in problems:
        print(f"FAIL {problem}", file=sys.stderr)
    print(
        "OK: every seeded bug matches the ground truth"
        if not problems
        else f"{len(problems)} mismatch(es)"
    )
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
