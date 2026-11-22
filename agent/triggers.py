"""Did a run's injected mistake actually reach the bug? (Decision OD-3.)

A seeded bug that needs a persona's mistake can only show when that mistake
happens where it matters. Counting any typo anywhere as a trigger understates
detection: a typo in the name field of a form that only checks the email
never reaches the bug. So a run counts as triggered only when the log shows
the mistake had its effect:

- data_loss_on_error, error_not_identified, error_not_actionable: a typo or
  skipped field happened, and later a submit on the same page was rejected
  (no request was sent and the goal was not reached).
- duplicate_submission: a doubled press (double_submit or impatient_retry)
  on a click that sent a request.
- no_way_back: a back press happened (the slip or the model's own).
- Every other signal needs no mistake: every run counts.

Read from the run log only, so `evaluate --rescore` recomputes it.
"""

from agent.detectors import RunLog
from agent.detectors.error_not_identified import is_submit

TYPING_SLIPS = {"typo", "skip_field"}
DOUBLE_PRESSES = {"double_submit", "impatient_retry"}
NEEDS_REJECTED_SUBMIT = {"data_loss_on_error", "error_not_identified", "error_not_actionable"}


def triggered(signal: str, run: RunLog) -> bool:
    if signal in NEEDS_REJECTED_SUBMIT:
        return _slip_then_rejected_submit(run)
    if signal == "duplicate_submission":
        sent = {s.step for s in run.submissions}
        return any(s.perturbation in DOUBLE_PRESSES and s.step in sent for s in run.steps)
    if signal == "no_way_back":
        return any(
            s.executed_action is not None and s.executed_action.action == "back" for s in run.steps
        )
    return True


def _slip_then_rejected_submit(run: RunLog) -> bool:
    sent = {s.step for s in run.submissions}
    slipped_on: str | None = None  # URL path of the page where the slip happened
    for step in run.steps:
        if step.step >= len(run.observations):
            break
        page = run.observations[step.step].url_path
        if step.perturbation in TYPING_SLIPS:
            slipped_on = page
            continue
        if slipped_on != page or step.goal_reached:
            continue
        if is_submit(run, step) and step.step not in sent:
            return True
    return False
