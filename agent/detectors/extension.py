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
P6 touch_imprecise: target_too_small (B19), mis_tap_consequence (B18); it
also uses P7's reflow_failure.
P10 slow_network: no_loading_feedback (B28), network_failure_silent (B29); it
also uses P1's duplicate_submission.
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


# The page-fact detectors below (structure, names, focus indicator, buried
# text, call to action, headings) report whether or not the persona finished:
# the fact is in the log either way. Severity says which: 4 when the task was
# blocked, 2 when the persona got through with friction (grounding.severity).

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
    """No headings and no landmarks to move by (WCAG 1.3.1, 2.4.1)."""
    nodes = _tree(run, 0)
    if not nodes:
        return None
    if any(n.role == "heading" or n.role in LANDMARKS for n in walk(nodes)):
        return None
    return make_finding(run, "no_structure", [0])


def unnamed_control(run: RunLog) -> Finding | None:
    """A control with no accessible name (WCAG 4.1.2)."""
    nodes = _tree(run, 0)
    if any(n.role in CONTROL_ROLES and not n.name for n in walk(nodes)):
        return make_finding(run, "unnamed_control", [0])
    return None


def image_only_info(run: RunLog) -> Finding | None:
    """An image with no text alternative (WCAG 1.1.1)."""
    nodes = _tree(run, 0)
    if any(n.role == "img" and not n.name for n in walk(nodes)):
        return make_finding(run, "image_only_info", [0])
    return None


# --- P5 keyboard only ------------------------------------------------------------


def focus_not_visible(run: RunLog) -> Finding | None:
    """Focus sat on an element with no visible indicator (WCAG 2.4.7)."""
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
    node (WCAG 2.4.6)."""
    critical = run.meta.get("critical_text")
    if not critical:
        return None
    for n in walk(_tree(run, 0)):
        text = n.text or ""
        if n.role in TEXT_ROLES and critical in text:
            if len(text[: text.index(critical)].split()) >= SKIM_WORDS:
                return make_finding(run, "key_info_buried", [0])
    return None


def cta_below_fold(run: RunLog) -> Finding | None:
    """The control named by the task's critical text starts below the first
    viewport (Nielsen #8)."""
    critical = run.meta.get("critical_text")
    if not critical or not run.facts or not run.facts[0]:
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
    "Other") (WCAG 2.4.6)."""
    vague = [
        n
        for n in walk(_tree(run, 0))
        if n.role == "heading" and GENERIC_HEADING.match((n.name or "").strip())
    ]
    return make_finding(run, "headings_not_descriptive", [0]) if len(vague) >= 2 else None


# --- P6 mobile touch -------------------------------------------------------------

MIN_TARGET_PX = 24  # WCAG 2.5.8


def target_too_small(run: RunLog) -> Finding | None:
    """A mis-tap happened on a target smaller than 24 CSS px on a side
    (WCAG 2.5.8)."""
    evidence = []
    for step in run.steps:
        k = step.step
        facts = run.facts[k] if k < len(run.facts) else None
        if step.perturbation != "mis_tap" or not facts:
            continue
        box = facts["boxes"].get(step.intended_action.ref)
        if box and min(box[2], box[3]) < MIN_TARGET_PX:
            evidence.append(k)
    return make_finding(run, "target_too_small", evidence) if evidence else None


def mis_tap_consequence(run: RunLog) -> Finding | None:
    """A mis-tap landed on another control and sent a request or changed a
    selection, with nothing asked first (WCAG 3.3.4)."""
    sent = {s.step for s in run.submissions}
    for step in run.steps:
        ex = step.executed_action
        if step.perturbation != "mis_tap" or ex is None or ex.ref == step.intended_action.ref:
            continue
        roles = {n.ref: n.role for n in walk(_tree(run, step.step)) if n.ref}
        if step.step in sent or roles.get(ex.ref) in ("radio", "checkbox", "option"):
            return make_finding(run, "mis_tap_consequence", [step.step])
    return None


# --- P10 slow connection ---------------------------------------------------------


def _network(run: RunLog, i: int) -> dict:
    return (run.network[i] if i < len(run.network) else None) or {}


def no_loading_feedback(run: RunLog) -> Finding | None:
    """After a click, the request was still waiting and the page showed no
    change at all: no busy state, status or disabled button (WCAG 4.1.3).
    The loop checks this right after each click (`silent_waits`); a look at
    a later step that finds the request pending and the page unchanged also
    counts."""
    for i in range(1, len(run.observations)):
        if _network(run, i).get("silent_waits", 0) > _network(run, i - 1).get("silent_waits", 0):
            return make_finding(run, "no_loading_feedback", [i - 1])
    for k in sorted({s.step for s in run.submissions}):
        if not _network(run, k + 1).get("pending"):
            continue
        before = run.full_trees[k] if k < len(run.full_trees) else None
        after = run.full_trees[k + 1] if k + 1 < len(run.full_trees) else None
        if before is not None and before == after:
            return make_finding(run, "no_loading_feedback", [k])
    return None


def _live_message(nodes: list[Node]) -> bool:
    """Some alert or status region on the page holds text."""
    for n in nodes:
        if n.role in LIVE_ROLES and (n.text or n.name or n.children):
            return True
        if _live_message(n.children):
            return True
    return False


def network_failure_silent(run: RunLog) -> Finding | None:
    """A submission failed and the page looks exactly as it did before the
    press: nothing says it did not go through (WCAG 4.1.3). A retry that
    fails again under an error message still on screen is not silent."""
    for i in range(1, len(run.observations)):
        if _network(run, i).get("failed", 0) > _network(run, i - 1).get("failed", 0):
            before = run.full_trees[i - 1] if i - 1 < len(run.full_trees) else None
            after = run.full_trees[i] if i < len(run.full_trees) else None
            if before is not None and before == after and not _live_message(_tree(run, i)):
                return make_finding(run, "network_failure_silent", [i - 1])
    return None


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
    target_too_small,
    mis_tap_consequence,
    no_loading_feedback,
    network_failure_silent,
]
