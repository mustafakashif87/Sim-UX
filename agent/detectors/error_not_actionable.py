"""`error_not_actionable` (B3): an error shows but names no field and no fix.

Spec, P1 table: error text exists but does not name the field or the fix.
Nielsen #9, WCAG 3.3.3 Error Suggestion. The spec lists it as model-judged;
this is a deterministic version (decided 22 Nov 2026), so it needs no second
model and its result does not depend on one:

After a submit attempt, the page shows an alert with text and at least one
field marked invalid, and for some invalid field the alert shares no content
word with that field's name ("Invalid input." vs "Phone number"), and the
alert gives no example ("like", "for example", "such as"). "Enter your name."
names the field; "Phone number must be 11 digits" does too.
"""

import re

from agent.contracts import Finding, Observation
from agent.detectors import RunLog, make_finding
from agent.detectors._tree import nodes
from agent.detectors.error_not_identified import is_submit

SIGNAL = "error_not_actionable"
_FIELD_ROLES = {"textbox", "searchbox", "combobox", "spinbutton"}
_FILLER = {"your", "the", "and", "for", "with", "enter", "this", "field", "please", "you"}
_EXAMPLE = re.compile(r"\blike\b|\bfor example\b|\be\.g\.|\bsuch as\b", re.IGNORECASE)


def _words(text: str) -> set[str]:
    return {w for w in re.findall(r"[a-z]+", text.lower()) if len(w) >= 3} - _FILLER


def vague_error(obs: Observation) -> str | None:
    """The alert text when it names none of the invalid fields, else None."""
    all_nodes = nodes(obs)
    alert = " ".join(
        n.text or n.name or "" for n in all_nodes if n.role == "alert" and (n.text or n.name)
    ).strip()
    invalid = [n.name or "" for n in all_nodes if n.role in _FIELD_ROLES and "invalid" in n.attrs]
    if not alert or not invalid or _EXAMPLE.search(alert):
        return None
    said = _words(alert)
    if any(not (_words(name) & said) for name in invalid):
        return alert
    return None


def error_not_actionable(run: RunLog) -> Finding | None:
    evidence = []
    for step in run.steps:
        if step.goal_reached or step.step + 1 >= len(run.observations):
            continue
        if is_submit(run, step) and vague_error(run.observations[step.step + 1]):
            evidence.append(step.step)
    return make_finding(run, SIGNAL, evidence) if evidence else None
