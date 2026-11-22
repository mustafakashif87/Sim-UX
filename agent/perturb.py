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
| mis_tap       | slip  | click, with boxes | lands on the nearest neighbour, or misses |
| capture       | slip  | click, with habit | goes to the control at the habitual spot  |

`mis_tap` (P6) needs the targets' bounding boxes, which the loop passes for
extension personas. Its chance grows as the target shrinks:
p = min(cap, base_rate * 44 / smaller side in CSS px) (Fitts's law; 44 px is
the platform guideline size). `impatient_retry` (P10) depends on what the
page did after the click, so the loop applies it (agent/loop.py).

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
MIS_TAP = "mis_tap"
CAPTURE = "capture"
IMPATIENT_RETRY = "impatient_retry"
GUIDELINE_PX = 44


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

    def apply(
        self, action: Action, refs: RefMap, boxes: dict | None = None, habit: dict | None = None
    ) -> Perturbed:
        """`boxes` maps refs to [x, y, width, height] (extension runs only);
        `habit` is P12's learned control: {"name", "center": [x, y]}."""
        if action.action == "give_up":
            return Perturbed(action)
        draw = self._rng.random()
        for name, rate in self._candidates(action, refs, boxes, habit):
            if draw < rate:
                if name == MIS_TAP:
                    return self._mis_tap(action, refs, boxes)
                if name == CAPTURE:
                    return Perturbed(
                        action.model_copy(update={"ref": _at_habit(action, refs, boxes, habit)}),
                        CAPTURE,
                    )
                return self._inject(name, action)
            draw -= rate
        return Perturbed(action)

    def _mis_tap_rate(self, action: Action, boxes: dict | None) -> float:
        c = self.config
        box = (boxes or {}).get(action.ref)
        if not c.mis_tap_base_rate or not box or min(box[2], box[3]) <= 0:
            return 0.0
        return min(c.mis_tap_cap, c.mis_tap_base_rate * GUIDELINE_PX / min(box[2], box[3]))

    def _mis_tap(self, action: Action, refs: RefMap, boxes: dict) -> Perturbed:
        """The tap lands on the nearest other operable element within reach,
        or on empty space (nothing happens)."""
        from agent.actions import INTERACTIVE_ROLES

        x, y, w, h = boxes[action.ref]
        cx, cy = x + w / 2, y + h / 2
        reach = self.config.mis_tap_reach_px
        best = None
        for ref, (bx, by, bw, bh) in boxes.items():
            if ref == action.ref or ref not in refs or refs[ref].role not in INTERACTIVE_ROLES:
                continue
            gap = max(bx - (x + w), x - (bx + bw), by - (y + h), y - (by + bh), 0)
            # nearest edge first, then nearest centre: where a thumb lands
            centre = ((bx + bw / 2 - cx) ** 2 + (by + bh / 2 - cy) ** 2) ** 0.5
            if gap <= reach and (best is None or (gap, centre, ref) < best):
                best = (gap, centre, ref)
        if best is None:
            return Perturbed(None, MIS_TAP, times=0)  # tapped empty space
        return Perturbed(action.model_copy(update={"ref": best[2]}), MIS_TAP)

    def _candidates(
        self, action: Action, refs: RefMap, boxes: dict | None = None, habit: dict | None = None
    ) -> list[tuple[str, float]]:
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
        if action.action == "click":
            out.append((MIS_TAP, self._mis_tap_rate(action, boxes)))
            if _at_habit(action, refs, boxes, habit):
                out.append((CAPTURE, c.capture_rate))
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


def _at_habit(action: Action, refs: RefMap, boxes: dict | None, habit: dict | None) -> str | None:
    """The operable control, other than the target, whose box holds the
    habitual position; None when there is none (no capture possible)."""
    from agent.actions import INTERACTIVE_ROLES

    if not habit or not boxes or action.ref is None or action.ref not in refs:
        return None
    if refs[action.ref].role != habit.get("role", refs[action.ref].role):
        return None  # a habit for pressing buttons does not capture a checkbox tick
    hx, hy = habit["center"]
    for ref, (x, y, w, h) in sorted(boxes.items()):
        if ref == action.ref or ref not in refs or refs[ref].role not in INTERACTIVE_ROLES:
            continue
        if x <= hx <= x + w and y <= hy <= y + h:
            return ref
    return None


def swap_adjacent(text: str, rng: random.Random) -> str:
    """Swap one random pair of adjacent, different characters ("form" -> "from")."""
    spots = [i for i in range(len(text) - 1) if text[i] != text[i + 1]]
    if not spots:
        return text
    i = rng.choice(spots)
    return text[:i] + text[i + 1] + text[i] + text[i + 2 :]
