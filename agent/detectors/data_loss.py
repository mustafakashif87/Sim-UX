"""`data_loss_on_error` (B1): an error on submit wipes fields the user had filled.

Spec, P1 table: field values before submit vs after the error response;
valid fields now empty. Nielsen #9, WCAG 3.3.7 Redundant Entry.

A step counts when all of these hold:
- the persona clicked or pressed a key (a submit attempt), and the goal was
  not reached;
- the page stayed on the same URL (a new page has empty fields by design);
- the page now shows an error: an alert with text, or a field marked invalid
  (without one, the user may have pressed a "Clear" button on purpose);
- a field that had a value before is now empty and is not itself marked
  invalid (clearing only the wrong field is acceptable).
"""

from agent.contracts import Finding, Observation
from agent.detectors import RunLog, make_finding
from agent.perception import parse_snapshot, walk

SIGNAL = "data_loss_on_error"
_FIELD_ROLES = {"textbox", "searchbox"}
_ERROR_ROLES = {"alert"}


def fields(obs: Observation) -> dict[tuple[str, int], tuple[str, bool]]:
    """Text fields by (name, nth with that name): (value, marked invalid)."""
    out: dict[tuple[str, int], tuple[str, bool]] = {}
    for node in walk(parse_snapshot(obs.tree)):
        if node.role in _FIELD_ROLES:
            name = node.name or ""
            nth = sum(1 for key in out if key[0] == name)
            out[(name, nth)] = ((node.text or "").strip(), "invalid" in node.attrs)
    return out


def shows_error(obs: Observation) -> bool:
    for node in walk(parse_snapshot(obs.tree)):
        if node.role in _ERROR_ROLES and (node.text or node.children or node.name):
            return True
        if node.role in _FIELD_ROLES and "invalid" in node.attrs:
            return True
    return False


def lost_fields(before: Observation, after: Observation) -> list[str]:
    """Names of fields that had a value and are now empty and not marked invalid."""
    now = fields(after)
    return [
        name
        for (name, nth), (value, _) in fields(before).items()
        if value and now.get((name, nth)) == ("", False)
    ]


def data_loss_on_error(run: RunLog) -> Finding | None:
    evidence = []
    for step in run.steps:
        executed = step.executed_action
        if executed is None or executed.action not in ("click", "press") or step.goal_reached:
            continue
        if step.step + 1 >= len(run.observations):
            continue
        before, after = run.observations[step.step], run.observations[step.step + 1]
        if before.url_path != after.url_path or not shows_error(after):
            continue
        if lost_fields(before, after):
            evidence.append(step.step)
    return make_finding(run, SIGNAL, evidence) if evidence else None
