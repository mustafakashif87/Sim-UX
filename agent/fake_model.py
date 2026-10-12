"""Scripted fake model: deterministic, offline, no API key.

Drives the loop in tests, in CI and as the demo's last fallback (spec:
Evaluation protocol, Unit tests). It sees only what a real model sees, the
Observation, and finds refs by reading the tree text, never the page.

    model = FakeModel([type_into("Full name", "Sara"), click("Send")])
"""

import json
import re
from collections.abc import Callable

from agent.contracts import Action, Observation

Step = Callable[[Observation], Action]


def find_ref(tree: str, role: str, name: str) -> str | None:
    """The ref of the first element with this role and exact name, if visible."""
    head = re.escape(f"- {role} {json.dumps(name, ensure_ascii=False)}")
    m = re.search(head + r"(?: \[[^\]]*\])*? \[ref=(e\d+)\]", tree)
    return m[1] if m else None


def _on(role: str, name: str, make: Callable[[str], Action]) -> Step:
    def step(obs: Observation) -> Action:
        ref = find_ref(obs.tree, role, name)
        if ref is None:
            return Action(thought=f"I cannot find {role} '{name}'", action="give_up")
        return make(ref)

    return step


def click(name: str, role: str = "button") -> Step:
    return _on(role, name, lambda ref: Action(thought=f"click {name}", action="click", ref=ref))


def type_into(name: str, text: str, role: str = "textbox") -> Step:
    return _on(
        role, name, lambda ref: Action(thought=f"fill {name}", action="type", ref=ref, text=text)
    )


def press(key: str) -> Step:
    return lambda obs: Action(thought=f"press {key}", action="press", key=key)


def back() -> Step:
    return lambda obs: Action(thought="go back", action="back")


def give_up() -> Step:
    return lambda obs: Action(thought="I give up", action="give_up")


def literal(action: Action) -> Step:
    """Send this exact action, e.g. one the validator must reject."""
    return lambda obs: action


class FakeModel:
    """Plays its script one step per call, then gives up when it runs out.

    `seen` keeps what each call received, so tests can check what the persona
    was shown, such as the history window.
    """

    model_id = "fake"

    def __init__(self, script: list[Step]):
        self._script = list(script)
        self.seen: list[tuple[Observation, list]] = []

    def next_action(self, task: str, observation: Observation, history: list) -> Action:
        self.seen.append((observation, list(history)))
        if len(self.seen) > len(self._script):
            return Action(thought="script finished", action="give_up")
        return self._script[len(self.seen) - 1](observation)
