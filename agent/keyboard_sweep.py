"""Keyboard sweep: the deterministic layer's keyboard check, no model.

Two signals (spec: deterministic layer; test-app SB-04 and SB-05):

- `keyboard_trap` (WCAG 2.1.2): pressing Tab from the top of the page never
  reaches some tabbable controls, because focus keeps cycling inside a small
  group of elements. A radio group counts as one Tab stop.
- `unreachable_control` (WCAG 2.1.1): a visible element has a click handler
  but cannot take keyboard focus, and no ancestor of it can.

Click handlers are read with the Chrome DevTools Protocol
(`DOMDebugger.getEventListeners`), so this needs Chromium. The sweep only
reads the page and presses Tab; it never activates anything.

    python -m agent.keyboard_sweep --page basket-a      # a test-app page
    python -m agent.keyboard_sweep --url https://...    # any page
"""

import argparse
import sys
from dataclasses import dataclass

from playwright.sync_api import Page

from agent.contracts import Finding
from grounding.ground import default_signal_map, severity, start_confidence

TRAP = "keyboard_trap"
UNREACHABLE = "unreachable_control"
PERSONA = "keyboard_sweep"

# Elements Tab can reach, in the browser's own terms. Run in the page.
_TABBABLE_JS = """() => {
  const visible = (el) => !!(el.offsetWidth || el.offsetHeight || el.getClientRects().length)
    && getComputedStyle(el).visibility !== 'hidden' && !el.closest('[inert]');
  const all = [...document.querySelectorAll('body *')];
  window.__simuxAll = all;
  return all.map((el, i) => ({
    i,
    tabbable: el.tabIndex >= 0 && !el.disabled && visible(el),
    visible: visible(el),
    // A radio group is one Tab stop; arrow keys move inside it.
    stop: el.type === 'radio' && el.name
      ? 'radio:' + (el.form ? el.form.id : '') + el.name
      : String(i),
    label: (el.getAttribute('aria-label') || el.innerText || el.value || el.id || el.tagName)
      .trim().slice(0, 40),
  }));
}"""
_ACTIVE_JS = """() => (window.__simuxAll || []).indexOf(document.activeElement)"""
_FOCUSABLE_UP_JS = """(i) => {
  for (let el = window.__simuxAll[i]; el && el !== document.body; el = el.parentElement) {
    if (el.tabIndex >= 0 && !el.disabled) return true;
  }
  return false;
}"""
_CLICK_EVENTS = {"click", "mousedown", "mouseup", "pointerdown", "pointerup"}


@dataclass(frozen=True)
class Issue:
    signal: str
    labels: list[str]  # the elements involved, as a person would name them
    presses: list[int]  # Tab presses that show it (1-based); [] when none apply


def sweep(page: Page, extra_presses: int = 4) -> list[Issue]:
    """Sweep the page as it is now. Leaves focus wherever the last Tab put it."""
    elements = page.evaluate(_TABBABLE_JS)
    tabbable = {e["i"] for e in elements if e["tabbable"]}
    label = {e["i"]: e["label"] for e in elements}
    stop = {e["i"]: e["stop"] for e in elements}
    issues = []

    page.evaluate("() => document.activeElement && document.activeElement.blur()")
    visited: list[int] = []
    for _ in range(2 * len(tabbable) + extra_presses):
        page.keyboard.press("Tab")
        visited.append(page.evaluate(_ACTIVE_JS))
    missed = {stop[i] for i in tabbable} - {stop[i] for i in visited if i >= 0}
    if missed:
        tail = visited[-len(tabbable) :]
        cycle = sorted({i for i in tail if i >= 0}, key=tail.index)
        presses = [n + 1 for n, i in enumerate(visited) if i in cycle][-4:]
        issues.append(Issue(TRAP, [label[i] for i in cycle], presses))

    unreachable = [
        e["i"]
        for e in elements
        if e["visible"]
        and not e["tabbable"]
        and _has_click_handler(page, e["i"])
        and not page.evaluate(_FOCUSABLE_UP_JS, e["i"])
    ]
    if unreachable:
        issues.append(Issue(UNREACHABLE, [label[i] for i in unreachable], []))
    return issues


def _has_click_handler(page: Page, index: int) -> bool:
    cdp = page.context.new_cdp_session(page)
    try:
        ref = cdp.send(
            "Runtime.evaluate", {"expression": f"window.__simuxAll[{index}]", "objectGroup": "sx"}
        )
        object_id = ref["result"].get("objectId")
        if not object_id:
            return False
        listeners = cdp.send("DOMDebugger.getEventListeners", {"objectId": object_id})
        return any(lst["type"] in _CLICK_EVENTS for lst in listeners["listeners"])
    finally:
        cdp.send("Runtime.releaseObjectGroup", {"objectGroup": "sx"})
        cdp.detach()


def findings(page_name: str, issues: list[Issue]) -> list[Finding]:
    """One Finding per issue. Evidence steps are the Tab presses that show it
    (press 0 stands for the static check). Severity 4: a keyboard user cannot
    finish the task."""
    signal_map = default_signal_map()
    return [
        Finding(
            finding_id=f"{PERSONA}-{page_name}-{issue.signal}",
            persona=PERSONA,
            page=page_name,
            signal=issue.signal,
            evidence_steps=issue.presses or [0],
            candidate_criteria=signal_map.candidates(issue.signal),
            severity=severity(task_completed=False, data_loss=False),
            confidence=start_confidence(signal_map.entry(issue.signal).type),
            baseline_reproduced=False,
        )
        for issue in issues
    ]


def main(argv: list[str] | None = None) -> int:
    from playwright.sync_api import sync_playwright

    from agent.browser import settle
    from agent.tasks import serve

    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    where = parser.add_mutually_exclusive_group(required=True)
    where.add_argument("--page", help="a test-app page, e.g. basket-a")
    where.add_argument("--url", help="any page URL")
    args = parser.parse_args(argv)

    def run(url: str, name: str) -> list[Finding]:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            page.goto(url)
            settle(page)
            issues = sweep(page)
            browser.close()
        for issue in issues:
            print(f"{issue.signal}: {', '.join(issue.labels)}")
        return findings(name, issues)

    if args.page:
        page_file = args.page if args.page.endswith(".html") else f"{args.page}.html"
        with serve() as base:
            found = run(base + page_file, page_file)
    else:
        found = run(args.url, args.url)
    for f in found:
        print(f.model_dump_json())
    if not found:
        print("No keyboard issues found.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
