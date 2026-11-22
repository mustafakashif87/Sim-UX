"""Per-step behaviours of the extension personas that span several steps
(persona catalogue, build steps 4 to 7). The loop calls them; each stays off
unless the persona's config turns it on, so P1 to P8 and P10 runs are
unchanged.

- World (P9, P14): the page clock. `think_time_s` moves it forward before
  every step after the first; `interruptions` idle (clock), reload or hide
  the page before a given step. An idle period is run in one-minute slices
  and what the page shows in each slice (dialogs, alerts, status) is logged,
  so a detector can tell whether a warning ever appeared.
- Escalation (P11): stuck = the page unchanged for `stuck_after` steps, or an
  error alert after two submit attempts. Then only help-seeking actions are
  accepted until a help control is used; after that, `after_help_steps` more.
- Habit (P12): the control used to submit on the flow's first screen and its
  position; shown as a note afterwards and used by the capture slip.
- klm_seconds (P13): Keystroke-Level Model time for the run (Card, Moran and
  Newell, 1983): M 1.35 s per action, P 1.1 s plus B 0.2 s per click,
  K 0.28 s per key or character, H 0.4 s per switch between mouse and keys.
"""

import math
import re
from functools import cache
from pathlib import Path

import yaml
from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import Page

from agent.contracts import Action, StepRecord
from agent.perception import RefMap, parse_snapshot, walk

LEXICON_PATH = Path(__file__).resolve().parents[1] / "grounding" / "help_lexicon.yaml"
_NOTICE_ROLES = {"dialog", "alertdialog", "alert", "status"}
IDLE_SLICE_S = 60


# --- P9, P14: clock and interruptions -------------------------------------------


class World:
    def __init__(self, env):
        self.env = env
        self.cold = False  # the coming step follows an interruption

    def install_clock(self, page: Page) -> None:
        """Before the first navigation, so the page's timers use the fake clock."""
        if self.env.needs_clock:
            page.clock.install()

    def before_step(self, page: Page, step: int) -> dict | None:
        """Think time and any interruption due before `step`; evidence or None."""
        self.cold = False
        if step > 0 and self.env.think_time_s:
            page.clock.run_for(int(self.env.think_time_s * 1000))
        due = [i for i in self.env.interruptions if i.at_step == step]
        if not due:
            return None
        events = []
        try:  # the page as the interruption found it, for the detectors
            before = page.locator("body").aria_snapshot(timeout=2000)
        except PlaywrightError:
            before = None
        for i in due:
            event = {"kind": i.kind, "seconds": i.seconds, "before": before}
            if i.kind == "idle":
                event["seen"] = _idle(page, i.seconds)
            elif i.kind == "reload":
                page.reload()
            elif i.kind == "tab_away":
                page.evaluate(_TAB_AWAY_JS)
            events.append(event)
        self.cold = True
        return {"interruptions": events}


_TAB_AWAY_JS = """() => {
  for (const state of ['hidden', 'visible']) {
    Object.defineProperty(document, 'visibilityState', {value: state, configurable: true});
    Object.defineProperty(document, 'hidden', {value: state === 'hidden', configurable: true});
    document.dispatchEvent(new Event('visibilitychange'));
  }
}"""


def _idle(page: Page, seconds: int) -> list[str]:
    """Move the clock `seconds` forward in slices; the notices shown in each."""
    seen: list[str] = []
    left = seconds
    while left > 0:
        step = min(IDLE_SLICE_S, left)
        page.clock.run_for(step * 1000)
        left -= step
        for text in notices(page):
            if text not in seen:
                seen.append(text)
    return seen


def notices(page: Page) -> list[str]:
    """Text of dialogs, alerts and status messages on the page now."""
    try:
        nodes = parse_snapshot(page.locator("body").aria_snapshot(timeout=2000))
    except PlaywrightError:
        return []
    out = []
    for n in walk(nodes):
        if n.role in _NOTICE_ROLES:
            text = " ".join(
                filter(None, [n.name, n.text, *(c.text or c.name or "" for c in walk(n.children))])
            ).strip()
            if text:
                out.append(text[:160])
    return out


# --- P11: escalation to help -----------------------------------------------------


@cache
def help_terms() -> tuple[str, ...]:
    data = yaml.safe_load(LEXICON_PATH.read_text(encoding="utf-8"))
    return tuple(sorted({t.lower() for t in data["terms"]}, key=len, reverse=True))


def is_help(name: str | None) -> bool:
    text = (name or "").lower()
    return any(re.search(rf"\b{re.escape(t)}\b", text) for t in help_terms())


class Escalation:
    def __init__(self, config):
        self.config = config  # Escalation config or None
        self.help_mode = False
        self.helped_at: int | None = None
        self._unchanged = 0
        self._last: str | None = None
        self._errors_after_submit = 0

    def update(self, content: str, tree: str, last: StepRecord | None) -> None:
        """Before the model acts: is the persona stuck now?"""
        if self.config is None or self.helped_at is not None:
            return
        self._unchanged = self._unchanged + 1 if content == self._last else 0
        self._last = content
        clicked = (
            last is not None
            and last.executed_action
            and last.executed_action.action
            in (
                "click",
                "press",
            )
        )
        if clicked and any(
            n.role == "alert" and (n.text or n.children) for n in walk(parse_snapshot(tree))
        ):
            self._errors_after_submit += 1
        if self._unchanged >= self.config.stuck_after - 1 or self._errors_after_submit >= 2:
            self.help_mode = True

    def validate(self, action: Action, refs: RefMap) -> str | None:
        if not self.help_mode or action.action in ("back", "scroll", "give_up"):
            return None
        if action.action == "click" and action.ref in refs and is_help(refs[action.ref].name):
            return None
        return (
            "you are stuck and looking for help: only help, contact or FAQ controls, back or scroll"
        )

    def after(self, step: int, action: Action | None, refs: RefMap, result: str) -> None:
        if self.help_mode and action is not None and action.action == "click" and result == "ok":
            if action.ref in refs and is_help(refs[action.ref].name):
                self.help_mode = False
                self.helped_at = step

    def out_of_budget(self, step: int) -> bool:
        return self.helped_at is not None and step > self.helped_at + self.config.after_help_steps

    def evidence(self, refs: RefMap) -> dict:
        return {
            "help_mode": self.help_mode,
            "helped_at": self.helped_at,
            "help_refs": sorted(r for r, t in refs.items() if is_help(t.name)),
        }


# --- P12: habit ------------------------------------------------------------------


class Habit:
    def __init__(self, prior_knowledge):
        self.on = prior_knowledge is not None
        self.learned: dict | None = None

    def learn(self, executed: Action | None, refs: RefMap, boxes: dict | None, sent: bool) -> None:
        """The first click that sent a request is the habit to remember."""
        if not self.on or self.learned or not sent or executed is None:
            return
        if executed.action != "click" or not boxes or executed.ref not in boxes:
            return
        x, y, w, h = boxes[executed.ref]
        target = refs[executed.ref]
        self.learned = {"name": target.name, "role": target.role, "center": [x + w / 2, y + h / 2]}

    def note(self, viewport: list | None) -> str | None:
        if not self.learned:
            return None
        where = ""
        if viewport:
            cx, cy = self.learned["center"]
            v = "top" if cy < viewport[1] / 2 else "bottom"
            hz = "left" if cx < viewport[0] / 2 else "right"
            where = f", at the {v} {hz}"
        return f"Last time you went on with '{self.learned['name']}'{where}."


# --- P13: budget and KLM ---------------------------------------------------------


def step_cap(persona, task) -> int:
    factor = persona.memory.max_steps_factor
    optimal = getattr(task, "optimal_steps", None)
    if factor and optimal:
        return math.ceil(optimal * factor)
    return persona.memory.max_steps


def klm_seconds(steps: list[StepRecord]) -> float:
    total, last_hand = 0.0, None
    for s in steps:
        a = s.executed_action
        if a is None:
            continue
        total += 1.35  # M: deciding
        hand = "mouse" if a.action in ("click", "scroll") else "keys"
        if last_hand and hand != last_hand:
            total += 0.4  # H: moving between mouse and keyboard
        last_hand = hand
        if a.action == "click":
            total += 1.1 + 0.2  # P + B
        elif a.action == "type":
            total += 0.28 * len(a.text or "")
        elif a.action == "press":
            total += 0.28
    return round(total, 2)
