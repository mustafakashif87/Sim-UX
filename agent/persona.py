"""Persona config: load and validate one YAML file from `personas/`.

A persona is a set of hard constraints on four axes, never a character in a
prompt (spec: Persona framework, Config schema). Each section of the config is
handed to the one module that enforces it: perception filters to
`browser.observe`, actions to `actions.validate`, memory to the loop and
perturbation to the perturbation layer.
"""

import hashlib
import json
import re
from pathlib import Path
from typing import Literal, Self

import yaml
from pydantic import ConfigDict, Field, field_validator, model_validator

from agent.actions import BROWSER_ACTIONS, ActionPolicy
from agent.contracts import ActionKind, Contract
from agent.perception import FILTERS

PERSONAS_DIR = Path(__file__).resolve().parents[1] / "personas"

# Key names Playwright's keyboard accepts, besides single characters. A typo
# such as "enter" must fail when the config loads, not halfway through a run.
_NAMED_KEYS = {
    "Backspace", "Tab", "Enter", "Escape", "Space", "Delete", "Insert",
    "Home", "End", "PageUp", "PageDown",
    "ArrowUp", "ArrowDown", "ArrowLeft", "ArrowRight",
    *(f"F{i}" for i in range(1, 13)),
}  # fmt: skip
_MODIFIERS = {"Shift", "Control", "Alt", "Meta", "ControlOrMeta"}
_KEY_CODE = re.compile(r"^(Key[A-Z]|Digit[0-9])$")  # physical key codes, e.g. KeyA


def is_key_name(key: str) -> bool:
    """True for "Enter", "a", "KeyA", "Shift+Tab"; False for "enter" or "Shift+"."""
    *mods, last = key.split("+")
    named = last in _NAMED_KEYS or len(last) == 1 or bool(_KEY_CODE.match(last))
    return all(m in _MODIFIERS for m in mods) and named


class Config(Contract):
    """Base for config sections. Strict types: YAML `true` or `"3"` is an error,
    never silently a rate of 1.0 or a number."""

    model_config = ConfigDict(strict=True)


class Perception(Config):
    filters: list[str] = Field(min_length=1)
    # Settings of individual filters (persona catalogue, P4 and P8).
    window_nodes: int = Field(default=15, ge=3)  # linear_window: nodes around the reading position
    rotor: list[
        Literal["headings", "landmarks"]
    ] = []  # linear_window: lists a screen reader offers
    skim_max_words: int = Field(default=8, ge=1)  # skim_text: words kept per text

    @field_validator("filters")
    @classmethod
    def _known_filters(cls, filters: list[str]) -> list[str]:
        unknown = [f for f in filters if f not in FILTERS]
        if unknown:
            raise ValueError(f"unknown perception filters: {unknown}")
        return filters


class Actions(Config):
    allowed: list[ActionKind] = Field(min_length=1)
    keys: list[str] = []
    # P4: clicks only on elements with an interactive role, as a screen reader
    # exposes them; a div with a click handler cannot be used.
    interactive_roles_only: bool = False
    # P5: `type` only into the focused element (a keyboard user types where focus is).
    type_focused_only: bool = False

    @model_validator(mode="after")
    def _valid_actions_and_keys(self) -> Self:
        not_browser = [a for a in self.allowed if a not in BROWSER_ACTIONS]
        if not_browser:
            raise ValueError(f"not browser actions (give_up is always allowed): {not_browser}")
        bad_keys = [k for k in self.keys if not is_key_name(k)]
        if bad_keys:
            raise ValueError(f"not Playwright key names: {bad_keys}")
        if self.keys and "press" not in self.allowed:
            raise ValueError("keys are listed but 'press' is not allowed")
        return self


class Memory(Config):
    history_turns: int = Field(ge=0)
    max_steps: int = Field(ge=1)


Rate = Field(default=0.0, ge=0.0, le=1.0)


class Perturbation(Config):
    """Chance of each injected mistake. All zero is no perturbation (baseline)."""

    seed: int = 0
    typo_rate: float = Rate
    skip_field_rate: float = Rate
    double_submit_rate: float = Rate
    back_press_rate: float = Rate
    # P6 mis_tap: p = min(cap, base_rate * 44 / smaller side in CSS px); the tap
    # lands on the nearest other interactive element within reach_px, or misses.
    mis_tap_base_rate: float = Rate
    mis_tap_cap: float = Rate
    mis_tap_reach_px: int = Field(default=12, ge=0)
    # P10: after a click that sends a request, click again while it is pending.
    impatient_retry_rate: float = Rate

    @model_validator(mode="after")
    def _one_mistake_per_step(self) -> Self:
        # At most one mistake per step (agent/perturb.py), so the rates that
        # can hit the same action must fit in one draw.
        typing = self.back_press_rate + self.skip_field_rate + self.typo_rate
        clicking = self.back_press_rate + self.double_submit_rate
        if max(typing, clicking) > 1 + 1e-9:  # tolerance: 0.33 + 0.56 + 0.11 > 1 in floats
            raise ValueError("rates that apply to the same action add up to more than 1")
        return self


class Viewport(Config):
    width: int = Field(ge=200)
    height: int = Field(ge=200)


class Network(Config):
    """What the connection does to the task's submission requests."""

    latency_ms: int = Field(default=0, ge=0, le=60_000)
    fail_rate: float = Rate  # chance a submission fails (network error)


class Environment(Config):
    """The fifth axis: what the world does to the user (persona catalogue,
    Framework changes). Enforced in browser.py and loop.py. The baseline keeps
    it: the world stays the same, only the persona's limits come off."""

    device: str | None = None  # a Playwright device name, e.g. "iPhone 13"
    viewport: Viewport | None = None
    text_scale: float = Field(default=1.0, ge=1.0, le=4.0)
    network: Network = Network()

    @field_validator("device")
    @classmethod
    def _known_device(cls, device: str | None) -> str | None:
        if device is not None:
            from agent.environment import DEVICES

            if device not in DEVICES:
                raise ValueError(f"unknown device {device!r}; one of {sorted(DEVICES)}")
        return device


class Persona(Config):
    id: str = Field(pattern=r"^[a-z][a-z0-9_]*$")
    perception: Perception
    actions: Actions
    memory: Memory
    perturbation: Perturbation = Perturbation()
    environment: Environment = Environment()
    task_types: list[str] = Field(min_length=1)

    @property
    def action_policy(self) -> ActionPolicy:
        return ActionPolicy(
            allowed=frozenset(self.actions.allowed),
            keys=frozenset(self.actions.keys),
            interactive_roles_only=self.actions.interactive_roles_only,
            type_focused_only=self.actions.type_focused_only,
        )

    @property
    def needs_evidence(self) -> bool:
        """Whether runs log the unfiltered tree and page geometry for the
        extension personas' detectors (P4 to P14). P1 to P3 do not need it."""
        filters = set(self.perception.filters) - {"full_tree", "vocab_filter"}
        p = self.perturbation
        return bool(
            filters
            or self.actions.interactive_roles_only
            or self.actions.type_focused_only
            or self.environment != Environment()
            or p.mis_tap_base_rate
            or p.impatient_retry_rate
        )

    @property
    def config_hash(self) -> str:
        """Fingerprint of the validated config, logged with every run.

        Hashes the values, not the file bytes, so comments and key order do
        not change it but any changed limit does.
        """
        canonical = json.dumps(self.model_dump(mode="json"), sort_keys=True)
        return hashlib.sha256(canonical.encode()).hexdigest()[:16]


Condition = Literal["persona", "baseline"]
CONDITIONS: tuple[Condition, ...] = ("persona", "baseline")

# Spec, Run conditions: the baseline has "full tree, full memory, no
# perturbation, generous budget". Generous is our number: twice the persona's
# step cap. Change it here and in the report together.
BASELINE_STEP_FACTOR = 2
BASELINE_KEYS = ("Tab", "Enter", "Escape")


def baseline(persona: Persona) -> Persona:
    """The same persona with every constraint off, for the Baseline condition.

    Full tree, every browser action, the whole run in memory, no perturbation
    and twice the steps. The id and the perturbation seed stay the same, so a
    baseline run differs from the persona run only in its constraints; the
    config hash changes, so the log shows which config ran.
    """
    steps = persona.memory.max_steps * BASELINE_STEP_FACTOR
    data = persona.model_dump()
    data["perception"] = {"filters": ["full_tree"]}
    data["actions"] = {
        "allowed": sorted(BROWSER_ACTIONS),
        "keys": list(dict.fromkeys([*persona.actions.keys, *BASELINE_KEYS])),
    }
    data["memory"] = {"history_turns": steps, "max_steps": steps}
    data["perturbation"] = {"seed": persona.perturbation.seed}  # every rate 0
    return Persona.model_validate(data)


def for_condition(persona: Persona, condition: Condition) -> Persona:
    if condition not in CONDITIONS:
        raise ValueError(f"unknown condition {condition!r}; one of {', '.join(CONDITIONS)}")
    return baseline(persona) if condition == "baseline" else persona


def load_persona(name_or_path: str | Path) -> Persona:
    """Load a persona by id (`error_prone`) or by path to its YAML file."""
    path = Path(name_or_path)
    if path.suffix not in (".yaml", ".yml"):
        if not re.fullmatch(r"[a-z][a-z0-9_]*", str(name_or_path)):
            raise ValueError(f"not a persona id: {name_or_path!r}")
        path = PERSONAS_DIR / f"{name_or_path}.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path.name}: a persona config must be a YAML mapping")
    persona = Persona.model_validate(data)
    if persona.id != path.stem:
        raise ValueError(f"{path.name}: id '{persona.id}' does not match the file name")
    return persona
