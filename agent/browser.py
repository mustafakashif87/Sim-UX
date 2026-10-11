"""Browser side of perception: snapshot a Playwright page and find refs again.

`observe` builds the Observation the model receives plus the private RefMap.
`locate` turns a ref back into a Playwright Locator for the action executor.
"""

from urllib.parse import urlparse

from playwright.sync_api import Locator, Page

from agent.contracts import FocusedElement, Observation
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
