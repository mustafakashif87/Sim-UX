"""Perturbation: seeded mistakes between the model's intent and the browser.

Runs after `actions.validate` and before `browser.act` (spec: Persona
framework, Perturbation axis). The model asks for one action; this layer
decides what actually reaches the browser. Both are logged in the StepRecord,
so every injected mistake is auditable.

Mistakes follow Reason's error taxonomy (spec: P1 Error-prone user):

| Name          | Kind  | Applies to        | Effect                                  |
| ------------- | ----- | ----------------- | --------------------------------------- |
| typo          | slip  | type              | two adjacent different characters swap  |
| skip_field    | lapse | type              | the action is dropped; field left as is |
| double_submit | slip  | click on a button | the click is executed twice             |
| back_press    | slip  | any but back      | a back press happens instead            |

At most one mistake per step, because a StepRecord has one `perturbation`.
One uniform draw per step is split into bands, one per mistake that applies,
so each mistake fires at exactly its configured rate among the actions it
applies to.
"""

import random
from dataclasses import dataclass

from agent.contracts import Action
from agent.perception import RefMap
from agent.persona import Perturbation

TYPO = "typo"
SKIP_FIELD = "skip_field"
DOUBLE_SUBMIT = "double_submit"
BACK_PRESS = "back_press"


@dataclass(frozen=True)
class Perturbed:
    """What reaches the browser. `executed` is None when the action was
    dropped; `times` says how often the loop executes it (0, 1 or 2)."""

    executed: Action | None
    perturbation: str | None = None
    times: int = 1


class Perturber:
    """Applies one persona's perturbation rates with its own seeded RNG.

    One Perturber per run. The evaluation protocol passes the run's seed
    (1 to 5); otherwise the config's seed is used. Same seed and same actions
    give the same mistakes, so runs replay exactly.
    """

    def __init__(self, config: Perturbation, seed: int | None = None):
        self.config = config
        self.seed = config.seed if seed is None else seed
        self._rng = random.Random(self.seed)

    def apply(self, action: Action, refs: RefMap) -> Perturbed:
        if action.action == "give_up":
            return Perturbed(action)
        draw = self._rng.random()
        for name, rate in self._candidates(action, refs):
            if draw < rate:
                return self._inject(name, action)
            draw -= rate
        return Perturbed(action)

    def _candidates(self, action: Action, refs: RefMap) -> list[tuple[str, float]]:
        """The mistakes that apply to this action, in a fixed order."""
        c = self.config
        out = []
        if action.action != "back":
            out.append((BACK_PRESS, c.back_press_rate))
        if action.action == "type":
            out += [(SKIP_FIELD, c.skip_field_rate), (TYPO, c.typo_rate)]
        target = refs.get(action.ref) if action.ref else None
        if action.action == "click" and target is not None and target.role == "button":
            out.append((DOUBLE_SUBMIT, c.double_submit_rate))
        return out

    def _inject(self, name: str, action: Action) -> Perturbed:
        match name:
            case "back_press":
                return Perturbed(Action(thought=action.thought, action="back"), BACK_PRESS)
            case "skip_field":
                return Perturbed(None, SKIP_FIELD, times=0)
            case "double_submit":
                return Perturbed(action, DOUBLE_SUBMIT, times=2)
            case "typo":
                typed = swap_adjacent(action.text, self._rng)
                if typed == action.text:
                    return Perturbed(action)  # nothing to swap, e.g. "a" or "aa"
                return Perturbed(action.model_copy(update={"text": typed}), TYPO)
        raise ValueError(f"unknown perturbation: {name}")


def swap_adjacent(text: str, rng: random.Random) -> str:
    """Swap one random pair of adjacent, different characters ("form" -> "from")."""
    spots = [i for i in range(len(text) - 1) if text[i] != text[i + 1]]
    if not spots:
        return text
    i = rng.choice(spots)
    return text[:i] + text[i + 1] + text[i] + text[i + 2 :]
