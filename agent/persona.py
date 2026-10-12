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
from typing import Self

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


class Persona(Config):
    id: str = Field(pattern=r"^[a-z][a-z0-9_]*$")
    perception: Perception
    actions: Actions
    memory: Memory
    perturbation: Perturbation = Perturbation()
    task_types: list[str] = Field(min_length=1)

    @property
    def action_policy(self) -> ActionPolicy:
        return ActionPolicy(
            allowed=frozenset(self.actions.allowed), keys=frozenset(self.actions.keys)
        )

    @property
    def config_hash(self) -> str:
        """Fingerprint of the validated config, logged with every run.

        Hashes the values, not the file bytes, so comments and key order do
        not change it but any changed limit does.
        """
        canonical = json.dumps(self.model_dump(mode="json"), sort_keys=True)
        return hashlib.sha256(canonical.encode()).hexdigest()[:16]


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
