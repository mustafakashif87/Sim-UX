"""`destructive_without_confirm` (B5): a destructive action happens at once.

Spec, P1 table: a destructive action completes with no confirmation step in
between. Nielsen #5 and #3, WCAG 3.3.4 Error Prevention.

A step counts when the persona clicked a control whose name says it destroys
something (delete, remove, erase, deactivate, discard, wipe), that click sent
a request, no earlier step had clicked such a control, and no dialog was open
before it. On a page that asks first, the request comes from the dialog's
"Yes" button in a later step, after the first destructive click. Typing a
confirmation word (cancel-*.html) is a confirmation step too: the button
there is "Submit", so it never counts.
"""

import re

from agent.contracts import Finding
from agent.detectors import RunLog, make_finding
from agent.detectors._tree import by_ref, nodes

SIGNAL = "destructive_without_confirm"
DESTRUCTIVE = re.compile(r"\b(delete|remove|erase|deactivate|discard|wipe)\b", re.IGNORECASE)
_DIALOG_ROLES = {"dialog", "alertdialog"}


def destructive_without_confirm(run: RunLog) -> Finding | None:
    sent = {s.step for s in run.submissions}
    asked_before = False
    for step in run.steps:
        executed = step.executed_action
        if executed is None or executed.action != "click":
            continue
        before = run.observations[step.step]
        target = by_ref(before, executed.ref)
        if target is None or not DESTRUCTIVE.search(target.name or ""):
            continue
        dialog_open = any(n.role in _DIALOG_ROLES for n in nodes(before))
        if step.step in sent and not asked_before and not dialog_open:
            return make_finding(run, SIGNAL, [step.step])
        asked_before = True
    return None
