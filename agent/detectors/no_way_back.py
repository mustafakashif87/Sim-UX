"""`no_way_back`: after going back, the persona cannot return to where it was.

Spec, P1 table: after an injected back press or change of mind, the prior
state cannot be restored within 3 steps. Nielsen #3 (no WCAG criterion).

For each executed `back` (the perturbation's slip or the model's own choice)
at step k, the prior state is the screen the persona saw at step k: URL and
tree, with every value it had typed. It is restored when that same screen
shows again after the back press or after any of the next RECOVERY_STEPS
actions. A back press with nowhere to go fails and leaves the screen as it
was, so it is restored at once.

Not judged when the run succeeded within RECOVERY_STEPS more steps: the
persona finished the task another way. A run that stopped early for any
other reason (give-up, step cap) counts: the way back was not found.
"""

from agent.contracts import Finding
from agent.detectors import RunLog, make_finding
from agent.detectors._tree import same_screen

SIGNAL = "no_way_back"
RECOVERY_STEPS = 3


def no_way_back(run: RunLog) -> Finding | None:
    evidence = []
    succeeded = run.meta.get("status") == "succeeded"
    last = len(run.observations) - 1
    for step in run.steps:
        executed = step.executed_action
        if executed is None or executed.action != "back" or step.step + 1 > last:
            continue
        prior = run.observations[step.step]
        window = run.observations[step.step + 1 : step.step + 2 + RECOVERY_STEPS]
        if any(same_screen(prior, later) for later in window):
            continue
        actions_after = len(run.steps) - step.step - 1
        if succeeded and actions_after <= RECOVERY_STEPS:
            continue
        evidence.append(step.step)
    return make_finding(run, SIGNAL, evidence) if evidence else None
