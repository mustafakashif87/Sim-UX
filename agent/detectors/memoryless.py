"""P2 Memoryless first-time user: `recall_required`, `lost_location`,
`no_progress_indicator` (spec, P2 table). All deterministic, from the step
history; P2 itself sees only the current page.

- `recall_required` (B7, Nielsen #6, WCAG 3.3.2): a reference-like value
  (letters and digits, e.g. RTN-48213) shows in an earlier observation, a
  later observation has an empty text field and no longer shows the value,
  and the run did not succeed. The clean page repeats the value beside the
  field, so it is still visible there.
- `lost_location` (B8, Nielsen #1, WCAG 2.4.2): the persona sees one screen
  three or more times, and two or more different screens of the flow share
  the same page title (from the title logged with each observation).
- `no_progress_indicator` (B9, Nielsen #1, WCAG 2.4.6): two or more
  different screens of one flow (different controls) carry the same
  headings, and no observation says "step N of M" or "N of M".
"""

import re
from collections import Counter

from agent.contracts import Finding, Observation
from agent.detectors import RunLog, make_finding
from agent.detectors._tree import nodes

_REFERENCE = re.compile(r"\b(?=[A-Z0-9-]*\d)(?=[A-Z0-9-]*[A-Z])[A-Z0-9]+(?:-[A-Z0-9]+)+\b")
_FIELD_ROLES = {"textbox", "searchbox"}
_CONTROL_ROLES = {"button", "textbox", "radio", "checkbox", "combobox", "link", "searchbox"}
_PROGRESS = re.compile(r"\b(?:step\s+)?\d+\s+of\s+\d+\b", re.IGNORECASE)


def _references(obs: Observation) -> set[str]:
    return set(_REFERENCE.findall(obs.tree))


def _has_empty_field(obs: Observation) -> bool:
    return any(n.role in _FIELD_ROLES and not (n.text or "").strip() for n in nodes(obs))


def recall_required(run: RunLog) -> Finding | None:
    if run.meta.get("status") == "succeeded":
        return None
    seen: set[str] = set()
    for i, obs in enumerate(run.observations):
        now = _references(obs)
        if seen - now and _has_empty_field(obs):
            return make_finding(run, "recall_required", [i])
        seen |= now
    return None


def _screen(obs: Observation) -> tuple:
    """A screen of a flow: its URL and its controls (role and name), without
    values, so typing into a field does not make a new screen."""
    controls = sorted({(n.role, n.name or "") for n in nodes(obs) if n.role in _CONTROL_ROLES})
    return (obs.url_path, tuple(controls))


def lost_location(run: RunLog) -> Finding | None:
    if not run.titles or len(run.titles) != len(run.observations):
        return None
    screens = [_screen(o) for o in run.observations]
    visits = Counter(screens)
    repeated = [s for s, n in visits.items() if n >= 3]
    if not repeated:
        return None
    titles: dict[str, set] = {}
    for screen, title in zip(screens, run.titles, strict=True):
        if title:
            titles.setdefault(title, set()).add(screen)
    if not any(len(group) >= 2 for group in titles.values()):
        return None
    evidence = [i for i, s in enumerate(screens) if s in repeated]
    return make_finding(run, "lost_location", evidence)


def no_progress_indicator(run: RunLog) -> Finding | None:
    if any(_PROGRESS.search(o.tree) for o in run.observations):
        return None
    first_seen: dict[tuple, int] = {}
    headings_of: dict[tuple, tuple] = {}
    for i, obs in enumerate(run.observations):
        screen = _screen(obs)
        if screen in first_seen:
            continue
        first_seen[screen] = i
        headings_of[screen] = tuple(n.name or "" for n in nodes(obs) if n.role == "heading")
    by_headings: dict[tuple, list[int]] = {}
    for screen, headings in headings_of.items():
        if headings:
            by_headings.setdefault(headings, []).append(first_seen[screen])
    evidence = sorted(i for steps in by_headings.values() if len(steps) >= 2 for i in steps)
    return make_finding(run, "no_progress_indicator", evidence) if evidence else None
