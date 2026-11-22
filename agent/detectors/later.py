"""Detectors for P9 and P11 to P13 (persona catalogue, build steps 4 to 7).
P14 has none of its own: it reuses P9's and P6's through the signal map.

P9 interrupted: timeout_no_warning (B26), data_lost_on_timeout (B26, B36),
state_lost_on_reload (B27), no_resume_cue.
P11 help_seeker: help_unreachable (B30), help_inconsistent (B31).
P12 habitual: inconsistent_identification (B32), inconsistent_navigation
(B33), capture_consequence (B32).
P13 power_user: no_enter_submit (B34), no_bulk_action (B35), excess_steps.
All deterministic; they read the logged evidence, not the persona's view.
"""

import re
from collections import defaultdict

from agent.contracts import Finding
from agent.detectors import RunLog, make_finding
from agent.detectors.data_loss import fields
from agent.detectors.extension import _tree
from agent.detectors.memoryless import _screen
from agent.perception import walk

ENDED = re.compile(r"session (has )?(ended|expired)|timed out|signed you out", re.IGNORECASE)
PROGRESS = re.compile(r"\b(step|question|page)\s+\d+\s+of\s+\d+\b", re.IGNORECASE)


def _failed(run: RunLog) -> bool:
    return run.meta.get("status") != "succeeded"


def _interruptions(run: RunLog) -> list[tuple[int, dict]]:
    return [(i, ev) for i, e in enumerate(run.entries) for ev in e.get("interruptions", [])]


# --- P9 ------------------------------------------------------------------------


def timeout_no_warning(run: RunLog) -> Finding | None:
    """During an idle period the session ended and nothing warned first: the
    first notice shown is the one that says it ended (WCAG 2.2.1)."""
    for i, ev in _interruptions(run):
        seen = ev.get("seen") or []
        if seen and ENDED.search(seen[0]):
            return make_finding(run, "timeout_no_warning", [i])
    return None


def data_lost_on_timeout(run: RunLog) -> Finding | None:
    """After the session ended, fields that held values are empty
    (WCAG 2.2.1, 2.2.5): the timeout cost the user their answers."""
    filled: set = set()
    ended_at = None
    for i, obs in enumerate(run.observations):
        full = run.full_trees[i] if i < len(run.full_trees) else None
        if ended_at is None and ENDED.search(full or obs.tree):
            ended_at = i
        now = fields(obs)
        if ended_at is None:
            filled |= {k for k, (v, _) in now.items() if v}
            continue
        if any(k in now and now[k][0] == "" for k in filled):
            return make_finding(run, "data_lost_on_timeout", [ended_at, i], data_loss=True)
    return None


def state_lost_on_reload(run: RunLog) -> Finding | None:
    """After a reload, a flow that had moved on is back on its first screen
    (WCAG 3.3.7)."""
    first = _screen(run.observations[0]) if run.observations else None
    for i, ev in _interruptions(run):
        if ev["kind"] != "reload" or i == 0 or i >= len(run.observations):
            continue
        after = _screen(run.observations[i])
        # The page just before the reload (logged by the harness), else the
        # last observation before it.
        prev = run.observations[i - 1]
        if ev.get("before"):
            prev = prev.model_copy(update={"tree": ev["before"]})
        before = _screen(prev)
        if before != first and after == first:
            return make_finding(run, "state_lost_on_reload", [i - 1, i], data_loss=True)
    return None


def no_resume_cue(run: RunLog) -> Finding | None:
    """After an interruption the persona came back to a page with no "step N
    of M" cue, and did not finish (WCAG 2.4.6)."""
    if not _failed(run):
        return None
    for i, _ in _interruptions(run):
        if i < len(run.observations) and not PROGRESS.search(run.observations[i].tree):
            return make_finding(run, "no_resume_cue", [i])
    return None


# --- P11 -----------------------------------------------------------------------


def help_unreachable(run: RunLog) -> Finding | None:
    """The persona got stuck and went looking for help, and the page offered
    no help, contact or FAQ control (WCAG 3.3.5)."""
    for i, e in enumerate(run.entries):
        h = e.get("help") or {}
        if h.get("help_mode") and not h.get("help_refs"):
            return make_finding(run, "help_unreachable", [i])
    return None


def help_inconsistent(run: RunLog) -> Finding | None:
    """Across the screens of one flow, the help control moves in reading
    order or disappears (WCAG 3.2.6)."""
    from agent.behaviour import is_help

    positions: dict[tuple, float | None] = {}
    first_step: dict[tuple, int] = {}
    for i, obs in enumerate(run.observations):
        screen = _screen(obs)
        if screen in positions or not any(role != "link" for role, _ in screen[1]):
            continue  # seen already, or not a step of the flow (no form controls)
        nodes = list(walk(_tree(run, i)))
        if not nodes:
            continue
        idx = next((k for k, n in enumerate(nodes) if n.ref and is_help(n.name)), None)
        positions[screen] = None if idx is None else idx / len(nodes)
        first_step[screen] = i
    values = list(positions.values())
    present = [v for v in values if v is not None]
    if not present or len(values) < 2:
        return None
    if len(present) < len(values) or max(present) - min(present) > 0.3:
        return make_finding(run, "help_inconsistent", sorted(first_step.values()))
    return None


# --- P12 -----------------------------------------------------------------------


def _clicked_name(run: RunLog, step) -> str | None:
    ex = step.executed_action
    if ex is None or ex.ref is None:
        return None
    return next((n.name for n in walk(_tree(run, step.step)) if n.ref == ex.ref), None)


def inconsistent_identification(run: RunLog) -> Finding | None:
    """Controls that send the same request (method and URL) carry different
    names on different screens (WCAG 3.2.4). Slipped clicks do not count."""
    names: dict[tuple, set] = defaultdict(set)
    steps: dict[tuple, list] = defaultdict(list)
    by_step = {s.step: s for s in run.steps}
    for sub in run.submissions:
        step = by_step.get(sub.step)
        if step is None or step.perturbation is not None:
            continue
        name = _clicked_name(run, step)
        if name:
            names[(sub.method, sub.url)].add(name)
            steps[(sub.method, sub.url)].append(sub.step)
    for key, found in names.items():
        if len(found) >= 2:
            return make_finding(run, "inconsistent_identification", sorted(set(steps[key])))
    return None


def inconsistent_navigation(run: RunLog) -> Finding | None:
    """The links of a navigation landmark come in a different order on a
    later screen (WCAG 3.2.3)."""
    orders: dict[str, tuple] = {}
    for i in range(len(run.observations)):
        for nav in (n for n in walk(_tree(run, i)) if n.role == "navigation"):
            links = tuple(n.name for n in walk(nav.children) if n.role == "link")
            key = nav.name or ""
            if key in orders and links and set(links) == set(orders[key]) and links != orders[key]:
                return make_finding(run, "inconsistent_navigation", [i])
            orders.setdefault(key, links)
    return None


def capture_consequence(run: RunLog) -> Finding | None:
    """A capture slip sent a request to a different address than the habit
    did (WCAG 3.3.4): the habitual spot now does something else."""
    subs = sorted(run.submissions, key=lambda s: s.step)
    if not subs:
        return None
    habit_url = subs[0].url
    for step in run.steps:
        if step.perturbation != "capture":
            continue
        if any(s.step == step.step and s.url != habit_url for s in subs):
            return make_finding(run, "capture_consequence", [step.step])
    return None


# --- P13 -----------------------------------------------------------------------


def no_enter_submit(run: RunLog) -> Finding | None:
    """Enter in a text field sent nothing and changed nothing (Nielsen #7)."""
    sent = {s.step for s in run.submissions}
    for step in run.steps:
        ex, k = step.executed_action, step.step
        if ex is None or ex.action != "press" or ex.key != "Enter" or k in sent:
            continue
        focused = run.observations[k].focused
        if focused is None or focused.role not in ("textbox", "searchbox", "spinbutton"):
            continue
        nxt = run.observations[k + 1] if k + 1 < len(run.observations) else None
        if nxt is not None and nxt.tree == run.observations[k].tree:
            return make_finding(run, "no_enter_submit", [k])
    return None


def _stem(name: str) -> str:
    return re.sub(r"\s*\d+\s*$", "", name).strip().lower()


def no_bulk_action(run: RunLog) -> Finding | None:
    """Five or more buttons do the same thing to different numbered items,
    and the persona did not finish within its budget (Nielsen #7)."""
    if not _failed(run):
        return None
    stems: dict[str, int] = defaultdict(int)
    for n in walk(_tree(run, 0)):
        if n.role == "button" and n.name and re.search(r"\d+\s*$", n.name):
            stems[_stem(n.name)] += 1
    if any(count >= 5 for count in stems.values()):
        return make_finding(run, "no_bulk_action", [0])
    return None


def excess_steps(run: RunLog) -> Finding | None:
    """The persona ran out of its budget, ceil(optimal x factor), on a task
    with a known shortest path (Nielsen #7)."""
    if run.meta.get("optimal_steps") and run.meta.get("status") == "step_cap":
        return make_finding(run, "excess_steps", [max(len(run.steps) - 1, 0)])
    return None


DETECTORS = [
    timeout_no_warning,
    data_lost_on_timeout,
    state_lost_on_reload,
    no_resume_cue,
    help_unreachable,
    help_inconsistent,
    inconsistent_identification,
    inconsistent_navigation,
    capture_consequence,
    no_enter_submit,
    no_bulk_action,
    excess_steps,
]
