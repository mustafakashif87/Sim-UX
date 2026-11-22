"""Detectors for the extension personas P4, P5, P7 and P8 (persona catalogue).

They read the evidence extension runs log with each observation and the
persona never sees: the unfiltered tree (`RunLog.full_trees`) and page facts
(`RunLog.facts`: bounding boxes by ref, scroll and client width, focus
visibility, obscured focus, clipped text, pointer-only elements). All are
deterministic. Where the catalogue asks that the persona failed, the run's
status says so.

P4 screen_reader: status_not_announced (B13), non_semantic_control (B14),
no_structure (B15), unnamed_control and image_only_info (SB-02, SB-01).
P5 keyboard_only: focus_order_illogical (B16), focus_not_visible (B17),
keyboard_trap_in_task (SB-04), keyboard_unreachable (SB-05).
P7 low_vision_zoom: reflow_failure (B20), focus_obscured (B21),
text_clipped (B22).
P8 skimmer: key_info_buried (B23), cta_below_fold (B24),
headings_not_descriptive (B25; rule-based, see below).
"""

import re

from agent.contracts import Finding
from agent.detectors import RunLog, make_finding
from agent.perception import Node, parse_snapshot, walk

LIVE_ROLES = {"status", "alert", "log", "marquee", "timer"}
LANDMARKS = {"banner", "navigation", "main", "contentinfo", "complementary", "region", "search"}
CONTROL_ROLES = {"button", "link", "textbox", "checkbox", "radio", "combobox", "searchbox"}
TEXT_ROLES = {"text", "paragraph"}


def _failed(run: RunLog) -> bool:
    return run.meta.get("status") != "succeeded"


def _tree(run: RunLog, i: int) -> list[Node]:
    text = run.full_trees[i] if i < len(run.full_trees) else None
    return parse_snapshot(text) if text else []


def _facts(run: RunLog) -> list[tuple[int, dict]]:
    return [(i, f) for i, f in enumerate(run.facts) if f]


def _texts_outside_live(nodes: list[Node], live: bool = False) -> set[str]:
    out: set[str] = set()
    for n in nodes:
        inside = live or n.role in LIVE_ROLES
        if n.role in TEXT_ROLES and n.text and not inside:
            out.add(n.text.strip())
        out |= _texts_outside_live(n.children, inside)
    return out


# --- P4 screen reader ----------------------------------------------------------


def status_not_announced(run: RunLog) -> Finding | None:
    """After a step that sent a request, new page text appears outside any
    live region, so a screen reader does not announce it (WCAG 4.1.3)."""
    sent = sorted({s.step for s in run.submissions})
    for k in sent:
        before, after = _tree(run, k), _tree(run, k + 1)
        if not before or not after:
            continue
        if _texts_outside_live(after) - _texts_outside_live(before):
            return make_finding(run, "status_not_announced", [k])
    return None


def non_semantic_control(run: RunLog) -> Finding | None:
    """The page has pointer-only elements with no role and the persona did
    not finish: the control it needed is not exposed (WCAG 4.1.2, 2.1.1)."""
    return _pointer_only(run, "non_semantic_control")


def _pointer_only(run: RunLog, signal: str) -> Finding | None:
    if not _failed(run):
        return None
    for i, f in _facts(run):
        if any(f.get("pointer_only") or []):
            return make_finding(run, signal, [i])
    return None


def no_structure(run: RunLog) -> Finding | None:
    """No headings and no landmarks to move by, and the persona did not
    finish (WCAG 1.3.1, 2.4.1)."""
    nodes = _tree(run, 0)
    if not nodes or not _failed(run):
        return None
    if any(n.role == "heading" or n.role in LANDMARKS for n in walk(nodes)):
        return None
    return make_finding(run, "no_structure", [0])


def unnamed_control(run: RunLog) -> Finding | None:
    """A control with no accessible name, and the persona did not finish."""
    nodes = _tree(run, 0)
    if _failed(run) and any(n.role in CONTROL_ROLES and not n.name for n in walk(nodes)):
        return make_finding(run, "unnamed_control", [0])
    return None


def image_only_info(run: RunLog) -> Finding | None:
    """An image with no text alternative, and the persona did not finish."""
    nodes = _tree(run, 0)
    if _failed(run) and any(n.role == "img" and not n.name for n in walk(nodes)):
        return make_finding(run, "image_only_info", [0])
    return None


# --- P5 keyboard only ------------------------------------------------------------


def focus_not_visible(run: RunLog) -> Finding | None:
    """Focus sat on an element with no visible indicator, and the persona did
    not finish (WCAG 2.4.7)."""
    if not _failed(run):
        return None
    for i, f in _facts(run):
        if f.get("focus_visible") is False:
            return make_finding(run, "focus_not_visible", [i])
    return None


def focus_order_illogical(run: RunLog) -> Finding | None:
    """A Tab press moved focus up the page to an element other than the
    first one Tab reaches (which is where focus wraps to), as positive
    tabindex values do (WCAG 2.4.3). Boxes come from the logged facts."""
    first_ref = None
    evidence = []
    for step in run.steps:
        ex = step.executed_action
        if ex is None or ex.action != "press" or ex.key != "Tab":
            continue
        k = step.step
        if k + 1 >= len(run.observations):
            continue
        before, after = run.observations[k].focused, run.observations[k + 1].focused
        f0 = run.facts[k] if k < len(run.facts) else None
        f1 = run.facts[k + 1] if k + 1 < len(run.facts) else None
        if after is not None and first_ref is None:
            first_ref = after.ref
        if before is None or after is None or not f0 or not f1:
            continue
        b0, b1 = f0["boxes"].get(before.ref), f1["boxes"].get(after.ref)
        if not b0 or not b1 or after.ref == first_ref:
            continue
        # compare page positions: box y is relative to the viewport
        y0, y1 = b0[1] + f0.get("scroll_y", 0), b1[1] + f1.get("scroll_y", 0)
        if y1 < y0 - 10:
            evidence.append(k)
    return make_finding(run, "focus_order_illogical", evidence) if evidence else None


TRAP_PRESSES = 6


def keyboard_trap_in_task(run: RunLog) -> Finding | None:
    """Six Tab presses in a row keep focus among two elements (WCAG 2.1.2):
    the sweep's trap, met during a task."""
    streak: list[tuple[int, str]] = []
    for step in run.steps:
        ex = step.executed_action
        k = step.step
        after = run.observations[k + 1].focused if k + 1 < len(run.observations) else None
        if ex is not None and ex.action == "press" and ex.key in ("Tab", "Shift+Tab") and after:
            streak.append((k, after.ref))
            recent = streak[-TRAP_PRESSES:]
            if len(recent) == TRAP_PRESSES and len({r for _, r in recent}) <= 2:
                return make_finding(run, "keyboard_trap_in_task", [s for s, _ in recent])
        else:
            streak = []
    return None


def keyboard_unreachable(run: RunLog) -> Finding | None:
    """Pointer-only elements no key reaches, and the persona did not finish
    (WCAG 2.1.1): the sweep's unreachable control, met during a task."""
    return _pointer_only(run, "keyboard_unreachable")


# --- P7 low vision -------------------------------------------------------------


def reflow_failure(run: RunLog) -> Finding | None:
    """The page scrolls sideways and a control lies wholly to the right of
    the viewport (WCAG 1.4.10)."""
    for i, f in _facts(run):
        if f.get("scroll_width", 0) <= f.get("client_width", 0) + 5 or not f.get("viewport"):
            continue
        width = f["viewport"][0]
        roles = {n.ref: n.role for n in walk(_tree(run, i)) if n.ref}
        if any(
            roles.get(ref) in CONTROL_ROLES and box[0] >= width for ref, box in f["boxes"].items()
        ):
            return make_finding(run, "reflow_failure", [i])
    return None


def focus_obscured(run: RunLog) -> Finding | None:
    """The focused element is wholly covered by another element (WCAG 2.4.11)."""
    for i, f in _facts(run):
        if f.get("focus_obscured"):
            return make_finding(run, "focus_obscured", [i])
    return None


def text_clipped(run: RunLog) -> Finding | None:
    """Text cut off by a box that hides its overflow (WCAG 1.4.4)."""
    for i, f in _facts(run):
        if f.get("clipped"):
            return make_finding(run, "text_clipped", [i])
    return None


# --- P8 skimmer ----------------------------------------------------------------

SKIM_WORDS = 8  # the skimmer's skim_max_words


def key_info_buried(run: RunLog) -> Finding | None:
    """The task's critical text starts past the words a skimmer reads in its
    node, and the persona did not finish (WCAG 2.4.6)."""
    critical = run.meta.get("critical_text")
    if not critical or not _failed(run):
        return None
    for n in walk(_tree(run, 0)):
        text = n.text or ""
        if n.role in TEXT_ROLES and critical in text:
            if len(text[: text.index(critical)].split()) >= SKIM_WORDS:
                return make_finding(run, "key_info_buried", [0])
    return None


def cta_below_fold(run: RunLog) -> Finding | None:
    """The control named by the task's critical text starts below the first
    viewport, and the persona did not finish (Nielsen #8)."""
    critical = run.meta.get("critical_text")
    if not critical or not _failed(run) or not run.facts or not run.facts[0]:
        return None
    f = run.facts[0]
    for n in walk(_tree(run, 0)):
        if n.role in CONTROL_ROLES and n.name == critical and n.ref in f["boxes"]:
            if f["viewport"] and f["boxes"][n.ref][1] >= f["viewport"][1]:
                return make_finding(run, "cta_below_fold", [0])
    return None


# The catalogue lists this as model-judged; this deterministic rule (decided
# 23 Nov 2026) flags headings that name no topic at all.
GENERIC_HEADING = re.compile(
    r"^(section|part|chapter|block)\s*\d+$|^(more( info(rmation)?)?|other|others|misc(ellaneous)?|"
    r"details|information|info|untitled|stuff|extras?)$",
    re.IGNORECASE,
)


def headings_not_descriptive(run: RunLog) -> Finding | None:
    """Two or more section headings name no topic ("Section 1", "More info",
    "Other"), and the persona did not finish (WCAG 2.4.6)."""
    if not _failed(run):
        return None
    vague = [
        n
        for n in walk(_tree(run, 0))
        if n.role == "heading" and GENERIC_HEADING.match((n.name or "").strip())
    ]
    return make_finding(run, "headings_not_descriptive", [0]) if len(vague) >= 2 else None


DETECTORS = [
    status_not_announced,
    non_semantic_control,
    no_structure,
    unnamed_control,
    image_only_info,
    focus_not_visible,
    focus_order_illogical,
    keyboard_trap_in_task,
    keyboard_unreachable,
    reflow_failure,
    focus_obscured,
    text_clipped,
    key_info_buried,
    cta_below_fold,
    headings_not_descriptive,
]
