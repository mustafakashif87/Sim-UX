"""`error_not_identified` (B2): a submit is rejected and nothing says so.

Spec, P1 table: invalid input submitted, but no new `alert` role,
`aria-invalid` or text near the field. Nielsen #9, WCAG 3.3.1 Error
Identification.

A step counts when all of these hold:
- the persona clicked a button or pressed Enter (a submit attempt) on a page
  with at least one filled text field, and the goal was not reached;
- no request was sent in that step (the submission was refused);
- the page after is the same screen as before: same URL, same tree;
- no error shows, before or after. An error already showing from an earlier
  attempt has identified the problem, so an unchanged page is fine then.
"""

from agent.contracts import Finding, StepRecord
from agent.detectors import RunLog, make_finding
from agent.detectors._tree import by_ref, same_screen
from agent.detectors.data_loss import fields, shows_error

SIGNAL = "error_not_identified"


def is_submit(run: RunLog, step: StepRecord) -> bool:
    executed = step.executed_action
    if executed is None:
        return False
    if executed.action == "press":
        return executed.key == "Enter"
    if executed.action == "click":
        target = by_ref(run.observations[step.step], executed.ref)
        return target is not None and target.role == "button"
    return False


def error_not_identified(run: RunLog) -> Finding | None:
    sent = {s.step for s in run.submissions}
    evidence = []
    for step in run.steps:
        if step.goal_reached or step.result != "ok" or step.step in sent:
            continue
        if step.step + 1 >= len(run.observations) or not is_submit(run, step):
            continue
        before, after = run.observations[step.step], run.observations[step.step + 1]
        if not any(value for value, _ in fields(before).values()):
            continue
        if same_screen(before, after) and not shows_error(before) and not shows_error(after):
            evidence.append(step.step)
    return make_finding(run, SIGNAL, evidence) if evidence else None
