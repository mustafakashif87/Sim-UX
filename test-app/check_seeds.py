"""Check every seeded bug against the ground truth in SEEDED_BUGS.md.

For each row of the Bugs table, the bug must be present on the buggy page and
absent on the clean page. Every task in tasks.yaml must also reach its goal on
both pages of its pair when done correctly, so the goal check is known to work.
On every page but B4's and B28's buggy ones, a double press on the final button must
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


def choose(page: Page, option: str) -> None:
    """Pick a radio option by its label, then Continue to the next step."""
    page.get_by_label(option).check()
    page.get_by_role("button", name="Continue").click()


def wizard_steps(page: Page, options: list[str]) -> list[tuple[str, str]]:
    """Walk a three-step wizard, picking `options` on steps 1 and 2. Returns the
    (document title, visible step heading) of each step as the user sees it."""
    seen = []
    for option in [*options, None]:
        heading = page.locator(".step:not([hidden]) h2")
        seen.append((page.title(), heading.inner_text().strip()))
        if option is not None:
            choose(page, option)
    return seen


# B11: words of the jargon instruction that a plain one would not use.
JARGON = {"notwithstanding", "hereinbefore", "hereinbelow", "effectuated", "forthwith"}


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


# --- B7 to B9: P2 Memoryless first-time user ------------------------------


@check("B7")
def reference_not_repeated(page: Page, posts: list[str]) -> bool:
    shown_first = "RTN-48213" in page.locator("#step1").inner_text()
    choose(page, "Stainless steel kettle")
    choose(page, "It arrived damaged")
    step3 = page.locator("#step3")
    step3.wait_for()
    return shown_first and "RTN-48213" not in step3.inner_text()


@check("B8")
def one_title_for_every_step(page: Page, posts: list[str]) -> bool:
    titles = {
        title for title, _ in wizard_steps(page, ["Yearly, $40 a year", "Saved card ending 4242"])
    }
    return len(titles) == 1


@check("B9")
def no_step_heading_or_indicator(page: Page, posts: list[str]) -> bool:
    steps = wizard_steps(page, ["Family, $7 a month for up to five people", "Every month"])
    headings = {heading for _, heading in steps}
    indicator = re.search(r"step \d+ of \d+", page.locator("main").inner_text(), re.I)
    return len(headings) == 1 and indicator is None


# --- B10 to B12: P3 Low-literacy or non-native reader ----------------------


@check("B10")
def jargon_button(page: Page, posts: list[str]) -> bool:
    return page.get_by_role("button", name="Effectuate remittance").count() == 1


@check("B11")
def jargon_instruction(page: Page, posts: list[str]) -> bool:
    words = set(re.findall(r"[a-z]+", page.locator("#instructions").inner_text().lower()))
    return bool(words & JARGON) and "STOP" in page.locator("#instructions").inner_text()


@check("B12")
def error_is_an_internal_code(page: Page, posts: list[str]) -> bool:
    page.get_by_label("Phone number").fill("0300 1234567")
    page.get_by_role("button", name="Save").click()
    return re.fullmatch(r"[A-Z]+(_[A-Z0-9]+)+", alert_text(page)) is not None


# --- B13 to B17, B20 to B25: extension personas P4, P5, P7, P8 ----------------

LIVE = "[role=status], [role=alert], [role=log], [aria-live]"


@check("B13")
def confirmation_not_live(page: Page, posts: list[str]) -> bool:
    page.get_by_label("Your feedback").fill("Fast delivery, thank you")
    page.get_by_role("button", name="Send feedback").click()
    message = page.get_by_text("Thanks, your feedback was sent.")
    message.wait_for()
    return not message.evaluate(f"el => !!el.closest({LIVE!r})")


@check("B14")
def size_picker_not_semantic(page: Page, posts: list[str]) -> bool:
    return page.get_by_role("radio").count() == 0 and page.get_by_text("UK 8").count() == 1


@check("B15")
def no_headings_or_landmarks(page: Page, posts: list[str]) -> bool:
    tree = page.locator("body").aria_snapshot()
    return re.search(r"- (heading|main|banner|navigation|contentinfo)\b", tree) is None


@check("B16")
def positive_tabindex(page: Page, posts: list[str]) -> bool:
    return page.evaluate(
        "() => [...document.querySelectorAll('[tabindex]')].some(e => e.tabIndex > 0)"
    )


@check("B17")
def focus_has_no_outline(page: Page, posts: list[str]) -> bool:
    page.keyboard.press("Tab")  # the site link
    page.keyboard.press("Tab")  # the email field
    return page.evaluate(
        """() => { const s = getComputedStyle(document.activeElement);
                   return s.outlineStyle === 'none' && s.boxShadow === 'none'; }"""
    )


@check("B20")
def scrolls_sideways_at_320(page: Page, posts: list[str]) -> bool:
    page.set_viewport_size({"width": 320, "height": 256})
    return page.evaluate("() => document.documentElement.scrollWidth > innerWidth + 5")


@check("B21")
def banner_covers_focused_field(page: Page, posts: list[str]) -> bool:
    page.set_viewport_size({"width": 320, "height": 256})
    field = page.get_by_label("Display name")
    field.focus()
    return field.evaluate(
        """el => { el.scrollIntoView({block: 'end'});
                   const r = el.getBoundingClientRect();
                   const x = r.left + r.width / 2, y = r.top + r.height / 2;
                   const hit = document.elementFromPoint(x, y);
                   return !!hit && hit !== el && !el.contains(hit); }"""
    )


@check("B22")
def deadline_clipped_at_200_percent(page: Page, posts: list[str]) -> bool:
    page.add_style_tag(content="html{font-size:200% !important}body{font-size:32px !important}")
    return page.evaluate(
        """() => { const n = document.querySelector('.notice');
                   return getComputedStyle(n).overflowY === 'hidden'
                       && n.scrollHeight > n.clientHeight + 2; }"""
    )


@check("B23")
def instruction_buried_in_paragraph(page: Page, posts: list[str]) -> bool:
    instruction = "Use the code from your email"
    paragraph = page.locator("p", has_text=instruction)
    text = paragraph.first.inner_text() if paragraph.count() else ""
    return len(text[: text.find(instruction)].split()) >= 8


@check("B24")
def call_to_action_below_fold(page: Page, posts: list[str]) -> bool:
    page.set_viewport_size({"width": 1280, "height": 720})
    box = page.get_by_role("button", name="Start free trial").bounding_box()
    return box is not None and box["y"] >= 720


@check("B25")
def headings_name_no_topic(page: Page, posts: list[str]) -> bool:
    names = [h.inner_text().strip() for h in page.locator("h2").all()]
    return sum(n in ("Section 1", "More info", "Other") for n in names) >= 2


@check("B18")
def remove_is_tiny_and_beside_plus(page: Page, posts: list[str]) -> bool:
    plus = page.get_by_role("button", name="Increase quantity").bounding_box()
    remove = page.get_by_role("button", name="Remove item").bounding_box()
    gap = remove["x"] - (plus["x"] + plus["width"])
    return min(remove["width"], remove["height"]) < 24 and gap < 12


@check("B19")
def delivery_options_are_tiny(page: Page, posts: list[str]) -> bool:
    row = page.locator("label", has_text="Standard (free)").bounding_box()
    return row["height"] < 24


@check("B28")
def pay_button_stays_enabled_and_silent(page: Page, posts: list[str]) -> bool:
    held = []
    page.unroute("**/api/**")
    page.route("**/api/**", lambda route: held.append(route))
    page.get_by_role("button", name="Pay now").click()
    page.wait_for_timeout(500)
    enabled = page.get_by_role("button", name="Pay now").is_enabled()
    status = page.get_by_role("status").inner_text().strip()
    for route in held:
        route.fulfill(status=200, body="ok")
    return enabled and not status


@check("B29")
def failure_leaves_page_unchanged(page: Page, posts: list[str]) -> bool:
    page.unroute("**/api/**")
    page.route("**/api/**", lambda route: route.abort("failed"))
    page.get_by_label("Meter reading").fill("48213")
    before = page.locator("body").aria_snapshot()
    page.get_by_role("button", name="Send reading").click()
    page.wait_for_timeout(500)
    return page.locator("body").aria_snapshot() == before


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


@happy("returns")
def return_item(page: Page, double: bool = False) -> None:
    choose(page, "Stainless steel kettle")
    choose(page, "It arrived damaged")
    page.get_by_label("Return reference").fill("RTN-48213")
    press(page.get_by_role("button", name="Book return"), double)


@happy("renew")
def renew(page: Page, double: bool = False) -> None:
    choose(page, "Yearly, $40 a year")
    choose(page, "Saved card ending 4242")
    page.get_by_label("I agree to the terms").check()
    press(page.get_by_role("button", name="Renew"), double)


@happy("upgrade")
def change_plan(page: Page, double: bool = False) -> None:
    choose(page, "Family, $7 a month for up to five people")
    choose(page, "Every month")
    press(page.get_by_role("button", name="Confirm change"), double)


@happy("transfer")
def send_money(page: Page, double: bool = False) -> None:
    page.get_by_label("Account number").fill("12345678")
    page.get_by_label("Amount in rupees").fill("500")
    press(page.locator("button[type=submit]"), double)  # its name is B10


@happy("cancel")
def end_membership(page: Page, double: bool = False) -> None:
    page.get_by_label("Confirmation").fill("STOP")
    press(page.get_by_role("button", name="Submit"), double)


@happy("phone")
def save_phone(page: Page, double: bool = False) -> None:
    page.get_by_label("Phone number").fill("03001234567")
    press(page.get_by_role("button", name="Save"), double)


@happy("feedback")
def send_feedback(page: Page, double: bool = False) -> None:
    page.get_by_label("Your feedback").fill("Fast delivery, thank you")
    press(page.get_by_role("button", name="Send feedback"), double)


@happy("size")
def add_trainers(page: Page, double: bool = False) -> None:
    page.get_by_text("UK 8", exact=True).click()  # a div or a radio's label
    press(page.get_by_role("button", name="Add to basket"), double)


@happy("policy")
def accept_policy(page: Page, double: bool = False) -> None:
    press(page.get_by_role("link", name="Accept the policy"), double)


@happy("filters")
def filter_kettles(page: Page, double: bool = False) -> None:
    page.get_by_label("Lowest price").fill("20")
    page.get_by_label("Highest price").fill("50")
    press(page.get_by_role("button", name="Apply filters"), double)


@happy("login")
def log_in(page: Page, double: bool = False) -> None:
    page.get_by_label("Email address").fill("sam.khan@example.com")
    page.get_by_label("Password").fill("Kettle-2026")
    press(page.get_by_role("button", name="Log in"), double)


@happy("invoice")
def pay_invoice(page: Page, double: bool = False) -> None:
    press(page.get_by_role("button", name="Pay invoice"), double)


@happy("profile")
def save_profile(page: Page, double: bool = False) -> None:
    field = page.get_by_label("Display name")
    field.fill("Sam K.")
    # Enter in the field, as the buggy page's banner may cover the button.
    field.press("Enter")
    if double:
        field.press("Enter")


@happy("notice")
def renew_permit(page: Page, double: bool = False) -> None:
    page.get_by_label("Renew by date").fill("15 December 2026")
    press(page.get_by_role("button", name="Request renewal"), double)


@happy("redeem")
def redeem_card(page: Page, double: bool = False) -> None:
    page.get_by_label("Gift card code").fill("GIFT-7731")
    press(page.get_by_role("button", name="Redeem"), double)


@happy("trial")
def start_trial(page: Page, double: bool = False) -> None:
    press(page.get_by_role("button", name="Start free trial"), double)


@happy("pricing")
def choose_annual_family(page: Page, double: bool = False) -> None:
    press(page.get_by_role("button", name="Choose Family, $70 a year"), double)


@happy("cart")
def two_kettles(page: Page, double: bool = False) -> None:
    page.get_by_role("button", name="Increase quantity").click()
    press(page.get_by_role("button", name="Go to checkout"), double)


@happy("shipping")
def free_delivery(page: Page, double: bool = False) -> None:
    page.get_by_label("Standard (free)").check()
    press(page.get_by_role("button", name="Pay now"), double)


@happy("payment")
def pay(page: Page, double: bool = False) -> None:
    press(page.get_by_role("button", name="Pay now"), double)


@happy("upload")
def send_reading(page: Page, double: bool = False) -> None:
    page.get_by_label("Meter reading").fill("48213")
    press(page.get_by_role("button", name="Send reading"), double)


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

        # Only B4's and B28's buggy pages may send twice (B28's bug is a button
        # that stays enabled while it waits); anywhere else a double press
        # would be a duplicate_submission finding missing from the ground truth.
        allowed = {buggy for bug, buggy, _ in rows if bug in ("B4", "B28")}
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
