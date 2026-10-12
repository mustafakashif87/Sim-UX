"""Browser side of the harness: everything that touches Playwright.

`observe` builds the Observation the model receives plus the private RefMap.
`locate` turns a ref back into a Playwright Locator.
`act` executes an action that `agent.actions.validate` has accepted.
"""

import time
from typing import Literal
from urllib.parse import urlparse

from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import Locator, Page

from agent.contracts import Action, FocusedElement, Observation
from agent.perception import (
    RefMap,
    RefTarget,
    apply_filters,
    assign_refs,
    parse_snapshot,
    render,
    walk,
)


def observe(
    page: Page, step: int, filters: list[str], notes: list[str] | None = None
) -> tuple[Observation, RefMap]:
    nodes = parse_snapshot(page.locator("body").aria_snapshot())
    # Refs are counted on the full tree so positions match the page, then the
    # filters run. Only refs still visible after filtering can be targeted:
    # what the persona cannot perceive, it cannot act on.
    all_refs = assign_refs(nodes)
    nodes = apply_filters(nodes, filters)
    refs = {n.ref: all_refs[n.ref] for n in walk(nodes) if n.ref in all_refs}

    observation = Observation(
        step=step,
        tree=render(nodes),
        focused=_focused(page, refs),
        url_path=urlparse(page.url).path,
        persona_notes=notes or [],
    )
    return observation, refs


def locate(page: Page, target: RefTarget) -> Locator:
    if target.name is not None:
        return page.get_by_role(target.role, name=target.name, exact=True).nth(target.nth)
    return page.get_by_role(target.role).nth(target.nth_in_role)


# Short enough that a click on a covered or disabled element fails within one
# step instead of stalling the run for Playwright's default 30 s.
ACTION_TIMEOUT_MS = 3000

# Upper bound on waiting for the page to settle after an action: a navigation
# to load, or a fetch-driven form to finish its requests. Hitting it is normal
# (a page that keeps polling) and is not an error.
SETTLE_TIMEOUT_MS = 2000


def act(
    page: Page,
    action: Action,
    refs: RefMap,
    timeout_ms: int = ACTION_TIMEOUT_MS,
    settle_ms: int = SETTLE_TIMEOUT_MS,
) -> Literal["ok", "error"]:
    """Execute a validated action, then wait for the page to settle.

    Returns "error" when the action could not take effect: a browser failure,
    a ref missing from the map, or `back` with no page to go back to. Never
    raises for these, so one bad step cannot crash a run.

    `scroll` with a ref scrolls that element into view; without one it scrolls
    down one viewport. `press` with a ref presses the key on that element;
    without one it goes to whatever has focus, as a keyboard user's would.
    """
    if action.action == "give_up":
        raise ValueError("give_up ends the run; it is not executed")
    track_requests(page)  # before the action, so requests it starts are seen
    if action.ref and action.ref not in refs:
        # validate() rejects this; reaching here means a harness bug, e.g. in
        # the perturbation layer. Fail the step, not the run.
        return "error"
    target = locate(page, refs[action.ref]) if action.ref else None
    try:
        match action.action:
            case "click":
                target.click(timeout=timeout_ms)
            case "type":
                target.fill(action.text, timeout=timeout_ms)
            case "press" if target:
                target.press(action.key, timeout=timeout_ms)
            case "press":
                page.keyboard.press(action.key)
            case "scroll" if target:
                target.scroll_into_view_if_needed(timeout=timeout_ms)
            case "scroll":
                page.mouse.wheel(0, page.viewport_size["height"] if page.viewport_size else 600)
            case "back":
                before = page.url
                # go_back returns None when there is no history entry; an
                # in-page (hash) back also returns None but changes the URL.
                if page.go_back(timeout=timeout_ms) is None and page.url == before:
                    return "error"
                # A run's tab starts on about:blank, so back from the first page
                # would leave the task. Treat it as having nowhere to go back to.
                if page.url == "about:blank":
                    page.go_forward(timeout=timeout_ms)
                    return "error"
    except PlaywrightError:
        return "error"
    if settle_ms > 0:  # Playwright reads a timeout of 0 as "wait forever"
        settle(page, settle_ms)
    return "ok"


# The page counts as settled once no request has been in flight for this long,
# which also lets a form's fetch handler update the page after its response.
QUIET_MS = 150
_POLL_MS = 25


def track_requests(page: Page) -> set:
    """Start counting this page's in-flight requests (once per page).

    Playwright's "networkidle" load state cannot be used: it fires once per
    navigation, so after a page has loaded it no longer waits for a form's
    fetch.
    """
    if not hasattr(page, "_simux_pending"):
        pending: set = set()
        page.on("request", lambda r: pending.add(r))
        page.on("requestfinished", lambda r: pending.discard(r))
        page.on("requestfailed", lambda r: pending.discard(r))
        page._simux_pending = pending
    return page._simux_pending


def settle(page: Page, timeout_ms: int = SETTLE_TIMEOUT_MS) -> None:
    """Wait until the page has loaded and no request has been in flight for
    QUIET_MS, up to timeout_ms. Hitting the bound is not an error."""
    pending = track_requests(page)
    deadline = time.monotonic() + timeout_ms / 1000
    try:
        page.wait_for_load_state("load", timeout=timeout_ms)
        quiet = 0
        while quiet < QUIET_MS and time.monotonic() < deadline:
            page.wait_for_timeout(_POLL_MS)  # lets Playwright deliver request events
            quiet = 0 if pending else quiet + _POLL_MS
    except PlaywrightError:
        pass


def goal_reached(page: Page, role: str, name: str) -> bool:
    """The harness's success check: a visible element with this role and name."""
    matches = page.get_by_role(role, name=name, exact=True)
    return any(matches.nth(i).is_visible() for i in range(matches.count()))


def _focused(page: Page, refs: RefMap) -> FocusedElement | None:
    if page.evaluate("() => !document.activeElement || document.activeElement === document.body"):
        return None
    snapshot = parse_snapshot(page.locator(":focus").aria_snapshot())
    if not snapshot:
        return None
    role, name = snapshot[0].role, snapshot[0].name
    for ref, target in refs.items():
        if (target.role, target.name) != (role, name):
            continue
        if locate(page, target).evaluate("el => el === document.activeElement"):
            return FocusedElement(ref=ref, role=role, name=name or "")
    return None
