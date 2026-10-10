"""The four interface contracts between SimUX modules.

Shapes follow docs/persona-design-spec.md, "Interface contracts". Change the
spec and these models together.
"""

from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

# Harness-assigned element reference, e.g. "e12". The model only ever sees
# these; the ref-to-locator map stays inside the harness.
ElementRef = Field(pattern=r"^e\d+$")

ActionKind = Literal["click", "type", "press", "scroll", "back", "give_up"]


class Contract(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class FocusedElement(Contract):
    ref: str = ElementRef
    role: str
    name: str


class Observation(Contract):
    """Perception -> model."""

    step: int = Field(ge=0)
    tree: str
    focused: FocusedElement | None = None
    url_path: str
    persona_notes: list[str] = []


class Action(Contract):
    """Model -> harness. Fields required by each action kind are enforced here."""

    thought: str
    action: ActionKind
    ref: str | None = ElementRef
    text: str | None = None
    key: str | None = None

    @model_validator(mode="after")
    def _fields_match_action(self) -> Self:
        needs_ref = self.action in ("click", "type")
        if needs_ref and self.ref is None:
            raise ValueError(f"'{self.action}' needs a ref")
        if self.action == "type" and self.text is None:
            raise ValueError("'type' needs text")
        if self.action == "press" and self.key is None:
            raise ValueError("'press' needs a key")
        if self.action in ("back", "give_up") and (self.ref or self.text or self.key):
            raise ValueError(f"'{self.action}' takes no ref, text or key")
        return self


class StepRecord(Contract):
    """Harness -> log. One JSONL line per step.

    intended_action is what the model asked for; executed_action is what reached
    the browser after perturbation (None when a perturbation dropped it).
    """

    run_id: str
    persona: str
    page: str
    step: int = Field(ge=0)
    observation_hash: str
    intended_action: Action
    executed_action: Action | None
    perturbation: str | None = None
    result: Literal["ok", "invalid", "error"]
    goal_reached: bool


class Citation(Contract):
    source: Literal["WCAG", "Nielsen"]
    criterion_id: str
    quote: str = Field(min_length=1)


class Finding(Contract):
    """Detector -> report."""

    finding_id: str
    persona: str
    page: str
    signal: str
    evidence_steps: list[int] = Field(min_length=1)
    candidate_criteria: list[str]
    citations: list[Citation] = []
    severity: int = Field(ge=1, le=4)
    confidence: float = Field(ge=0.0, le=1.0)
    baseline_reproduced: bool

    @model_validator(mode="after")
    def _citations_within_candidates(self) -> Self:
        outside = {c.criterion_id for c in self.citations} - set(self.candidate_criteria)
        if outside:
            raise ValueError(f"citations outside candidate criteria: {sorted(outside)}")
        return self
