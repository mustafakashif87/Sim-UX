"""Check every seeded bug against the ground truth in SEEDED_BUGS.md.

For each row of the Bugs table, the bug must be present on the buggy page and
absent on the clean page. Every task in tasks.yaml must also reach its goal on
both pages of its pair when done correctly, so the goal check is known to work.
On every page but B4's buggy one, a double press on the final button must
send one submission, so P1's injected double press cannot produce a
duplicate_submission finding the ground truth does not list.
Exits 1 on any mismatch, or when a row or task has no check here (or the other
way round), so CI's `seeds` job fails instead of trusting a stale ground truth.

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

import yaml
from playwright.sync_api import Browser, Page, sync_playwright
from playwright.sync_api import TimeoutError as PlaywrightTimeout

APP_DIR = Path(__file__).resolve().parent
GROUND_TRUTH = APP_DIR / "SEEDED_BUGS.md"
TASKS = APP_DIR / "tasks.yaml"
MAX_TABS = 25

# A check gets a fresh page and the bodies of the POSTs it has sent so far,
# and returns True when the bug is present on it.
Check = Callable[[Page, list[str]], bool]
CHECKS: dict[str, Check] = {}

# A happy path completes a task the way a careful user would; with
# double=True its final press is doubled, as P1's perturbation does it.
HappyPath = Callable[[Page, bool], None]
HAPPY: dict[str, HappyPath] = {}


def check(bug_id: str):
    def register(fn: Check) -> Check:
        CHECKS[bug_id] = fn
        return fn

    return register


def happy(task_id: str):
    def register(fn: HappyPath) -> HappyPath:
        HAPPY[task_id] = fn
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


def press(button, double: bool = False) -> None:
    """Click, and with double=True click again straight after, as the
    perturbation layer does. A disabled second press is the page working."""
    button.click()
    if double:
        try:
            button.click(timeout=500)
        except PlaywrightTimeout:
            pass


def reached_goal(page: Page, role: str, name: str, timeout_ms: int = 3000) -> bool:
    """The harness's goal check (agent.browser.goal_reached), with a wait."""
    try:
        page.get_by_role(role, name=name, exact=True).first.wait_for(timeout=timeout_ms)
        return True
    except PlaywrightTimeout:
        return False


def alert_text(page: Page, timeout_ms: int = 3000) -> str:
    """Text of the first alert that has any, or "" if none appears."""
    alert = page.get_by_role("alert").filter(has_text=re.compile(r"\S")).first
    try:
        alert.wait_for(timeout=timeout_ms)
    except PlaywrightTimeout:
        return ""
    return alert.inner_text().strip()


def shows_error(page: Page) -> bool:
    """An alert with text, or a field marked invalid (as the P1 detectors see it)."""
    if alert_text(page, timeout_ms=500):
        return True
    return page.locator("[aria-invalid=true]").count() > 0


def fill_delivery_address(page: Page) -> None:
    """Checkout step 1, filled correctly, then on to step 2."""
    page.get_by_label("Full name").fill("Sam Khan")
    page.get_by_label("Street address", exact=True).fill("12 Canal Road")
    page.get_by_label("City", exact=True).fill("Lahore")
    page.get_by_role("button", name="Continue").click()


# --- SB-01 to SB-05: deterministic-layer fixtures --------------------------


@check("SB-01")
def image_without_alt(page: Page, posts: list[str]) -> bool:
    return has_unnamed(page, "img")


@check("SB-02")
def button_without_name(page: Page, posts: list[str]) -> bool:
    return has_unnamed(page, "button")


@check("SB-03")
def field_without_label(page: Page, posts: list[str]) -> bool:
    return has_unnamed(page, "textbox")


@check("SB-04")
def focus_trap(page: Page, posts: list[str]) -> bool:
    return not tab_to_and_activate(page, "button[type=submit]")


@check("SB-05")
def mouse_only_control(page: Page, posts: list[str]) -> bool:
    return not tab_to_and_activate(page, "#confirm")


# --- B1 to B6: P1 Error-prone user -----------------------------------------


@check("B1")
def form_clears_on_error(page: Page, posts: list[str]) -> bool:
    page.get_by_label("Full name").fill("Sam Khan")
    page.get_by_label("Email address").fill("sam.khan")  # no @: invalid
    page.get_by_role("button", name="Create account").click()
    alert_text(page)
    return page.get_by_label("Full name").input_value() == ""


@check("B2")
def invalid_input_rejected_silently(page: Page, posts: list[str]) -> bool:
    page.get_by_label("Email address").fill("sam.khan")
    page.get_by_role("button", name="Subscribe").click()
    page.wait_for_timeout(500)
    return not posts and not shows_error(page)


@check("B3")
def error_does_not_name_field(page: Page, posts: list[str]) -> bool:
    page.get_by_label("Your name").fill("Sam Khan")
    page.get_by_label("Phone number").fill("12345")
    page.get_by_role("button", name="Request callback").click()
    return "phone" not in alert_text(page).lower()


@check("B4")
def double_submit_sends_twice(page: Page, posts: list[str]) -> bool:
    press(page.get_by_role("button", name="Place order"), double=True)
    page.wait_for_timeout(300)
    return len(posts) >= 2


@check("B5")
def deletes_without_confirmation(page: Page, posts: list[str]) -> bool:
    page.get_by_role("button", name="Delete account").click()
    page.wait_for_timeout(500)
    return bool(posts)


@check("B6")
def asks_again_for_address(page: Page, posts: list[str]) -> bool:
    fill_delivery_address(page)
    page.get_by_role("button", name="Continue").click()  # step 2: keep the default
    billing = page.get_by_label("Billing street address")
    billing.wait_for()
    return billing.input_value() == ""


# --- happy paths: every task in tasks.yaml reaches its goal on both pages ---


@happy("signup")
def sign_up(page: Page, double: bool = False) -> None:
    page.get_by_label("Full name").fill("Sam Khan")
    page.get_by_label("Email address").fill("sam.khan@example.com")
    press(page.get_by_role("button", name="Create account"), double)


@happy("subscribe")
def subscribe(page: Page, double: bool = False) -> None:
    page.get_by_label("Email address").fill("sam.khan@example.com")
    press(page.get_by_role("button", name="Subscribe"), double)


@happy("callback")
def request_callback(page: Page, double: bool = False) -> None:
    page.get_by_label("Your name").fill("Sam Khan")
    page.get_by_label("Phone number").fill("03001234567")
    press(page.get_by_role("button", name="Request callback"), double)


@happy("order")
def place_order(page: Page, double: bool = False) -> None:
    press(page.get_by_role("button", name="Place order"), double)


@happy("account")
def delete_account(page: Page, double: bool = False) -> None:
    press(page.get_by_role("button", name="Delete account"), double)
    confirm = page.get_by_role("button", name="Yes, delete my account")
    try:
        confirm.wait_for(timeout=1000)
    except PlaywrightTimeout:
        return  # this version has no confirmation step
    press(confirm, double)


@happy("checkout")
def check_out(page: Page, double: bool = False) -> None:
    fill_delivery_address(page)
    page.get_by_role("button", name="Continue").click()
    for label, value in [("Billing street address", "12 Canal Road"), ("Billing city", "Lahore")]:
        field = page.get_by_label(label)
        if not field.input_value():
            field.fill(value)
    press(page.get_by_role("button", name="Place order"), double)


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


def _open(browser: Browser, url: str) -> tuple[Page, list[str]]:
    """A fresh page whose POSTs to api/ are answered with 200 and recorded,
    as the harness does with a task's endpoint."""
    page = browser.new_page()
    posts: list[str] = []

    def answer(route) -> None:
        if route.request.method == "POST":
            posts.append(route.request.post_data or "")
        route.fulfill(status=200, body="ok")

    page.route("**/api/**", answer)
    page.goto(url)
    return page, posts


def _present(browser: Browser, base: str, name: str, fn: Check) -> bool:
    page, posts = _open(browser, f"{base}/{name}")
    try:
        return fn(page, posts)
    finally:
        page.close()


def _completes(browser: Browser, base: str, name: str, task: dict) -> bool:
    page, _ = _open(browser, f"{base}/{name}")
    try:
        HAPPY[task["id"]](page, False)
        return reached_goal(page, task["goal"]["role"], task["goal"]["name"])
    finally:
        page.close()


def _submissions_on_double_press(browser: Browser, base: str, name: str, task: dict) -> int:
    """Submissions sent when the final press is doubled. Every POST is held
    unanswered until both presses are done, as a slow server would, so a page
    that hides its form once answered still shows whether it guards the
    second press. Without the hold the result depends on timing."""
    page = browser.new_page()
    held = []

    def hold(route) -> None:
        if route.request.method == "POST":
            held.append(route)
        else:
            route.fulfill(status=200, body="ok")

    page.route("**/api/**", hold)
    try:
        page.goto(f"{base}/{name}")
        HAPPY[task["id"]](page, True)
        page.wait_for_timeout(300)
        for route in held:
            route.fulfill(status=200, body="ok")
        reached_goal(page, task["goal"]["role"], task["goal"]["name"])
        return len(held)
    finally:
        page.close()


def main() -> int:
    rows = ground_truth()
    tasks = yaml.safe_load(TASKS.read_text(encoding="utf-8"))
    row_ids = {r[0] for r in rows}
    task_ids = {t["id"] for t in tasks}
    problems = [f"{bug}: in SEEDED_BUGS.md but has no check" for bug in row_ids - CHECKS.keys()]
    problems += [
        f"{bug}: has a check but no row in SEEDED_BUGS.md" for bug in CHECKS.keys() - row_ids
    ]
    problems += [f"task {t}: in tasks.yaml but has no happy path" for t in task_ids - HAPPY.keys()]
    problems += [f"happy path {t}: no task in tasks.yaml" for t in HAPPY.keys() - task_ids]

    server = _serve()
    base = f"http://127.0.0.1:{server.server_port}"
    with sync_playwright() as p:
        browser = p.chromium.launch()

        print(f"{'bug':<6} {'buggy page':<20} {'present':<8} {'clean page':<20} present")
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

        print(f"\n{'task':<10} {'page':<20} goal reached")
        for task in tasks:
            if task["id"] not in HAPPY:
                continue
            for name in task["pages"]:
                done = _completes(browser, base, name, task)
                print(f"{task['id']:<10} {name:<20} {done}")
                if not done:
                    problems.append(f"task {task['id']}: goal not reached on {name}")

        # Only B4's buggy page may send twice; anywhere else a double press
        # would be a duplicate_submission finding missing from the ground truth.
        allowed = {buggy for bug, buggy, _ in rows if bug == "B4"}
        print(f"\n{'task':<10} {'page':<20} submissions on a double press")
        for task in tasks:
            if task["id"] not in HAPPY:
                continue
            for name in task["pages"]:
                sent = _submissions_on_double_press(browser, base, name, task)
                print(f"{task['id']:<10} {name:<20} {sent}")
                if sent != 1 and name not in allowed:
                    problems.append(f"task {task['id']}: {sent} submissions on {name}")

        browser.close()
    server.shutdown()

    for problem in problems:
        print(f"FAIL {problem}", file=sys.stderr)
    if problems:
        print(f"{len(problems)} mismatch(es)")
        return 1
    print("OK: every seeded bug matches the ground truth and every goal is reachable")
    return 0


if __name__ == "__main__":
    sys.exit(main())
