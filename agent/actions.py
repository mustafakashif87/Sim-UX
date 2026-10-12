"""Action space: decide whether the model's Action may reach the browser.

Pure functions, no browser. The persona's whitelist is enforced here, in code,
never in the prompt (spec: Persona framework, Action space axis). Execution of
a valid action is in `agent/browser.py` (`act`).

Refs are checked against the current RefMap, which holds only the refs the
persona can perceive after filtering: what it cannot see, it cannot act on.
"""

from dataclasses import dataclass

from agent.contracts import Action, ActionKind
from agent.perception import RefMap

# Actions the model can ask the browser to perform. `give_up` is not one: the
# model may always give up, and the loop ends the run instead of executing it.
BROWSER_ACTIONS: frozenset[ActionKind] = frozenset({"click", "type", "press", "scroll", "back"})


@dataclass(frozen=True)
class ActionPolicy:
    """A persona's action axis: which actions and which keys it may use."""

    allowed: frozenset[ActionKind]
    keys: frozenset[str]

    def __post_init__(self):
        unknown = self.allowed - BROWSER_ACTIONS
        if unknown:
            raise ValueError(f"unknown actions in policy: {sorted(unknown)}")


def validate(action: Action, policy: ActionPolicy, refs: RefMap) -> str | None:
    """Return why the action is invalid, or None if it may be executed.

    The reason is for the step log and persona notes; it never names a locator.
    """
    if action.action == "give_up":
        return None
    if action.action not in policy.allowed:
        return f"action '{action.action}' is not available"
    if action.ref is not None and action.ref not in refs:
        return f"no element {action.ref} on this page"
    if action.action == "press" and action.key not in policy.keys:
        return f"key '{action.key}' is not available"
    return None
