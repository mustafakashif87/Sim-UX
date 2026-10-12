"""The agent loop: one run of one persona on one task.

Each step: observe the page, ask the model for an action, validate it against
the persona's whitelist, perturb it, execute it, write a StepRecord and check
the goal (spec: Persona framework, flowchart). The harness decides success:
the model can give up but cannot declare success.

The persona config sets every limit here: perception filters, action
whitelist, history window, step cap and perturbation rates. None of them is
in the prompt.
"""

import hashlib
import importlib.metadata
import json
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal, Protocol
from urllib.parse import urlparse

from playwright.sync_api import Page

from agent.actions import validate
from agent.browser import act, goal_reached, observe, settle
from agent.contracts import Action, Observation, StepRecord
from agent.perception import RefMap
from agent.persona import Persona
from agent.perturb import SKIP_FIELD, Perturbed, Perturber

RunStatus = Literal["succeeded", "gave_up", "step_cap", "crashed"]

# The second click of a double submit comes straight after the first, as a
# real double press would. On a page that disables its button after one press
# the second click finds it disabled; that is the page working, not an error.
SECOND_CLICK_TIMEOUT_MS = 500


@dataclass(frozen=True)
class Goal:
    """Harness-side success check: a visible element with this role and name."""

    role: str
    name: str


@dataclass(frozen=True)
class Task:
    id: str
    url: str
    text: str  # what the user wants, as the model reads it; never names a bug
    goal: Goal


@dataclass(frozen=True)
class Turn:
    """One past step as the model may remember it: what it saw, what it asked
    for and whether that was possible. What was actually executed is not
    included; the persona only sees its consequences in later observations."""

    observation: Observation
    action: Action
    result: Literal["ok", "invalid", "error"]


class Model(Protocol):
    """Picks the next action. FakeModel for tests, an LLM client for real runs."""

    model_id: str

    def next_action(self, task: str, observation: Observation, history: list[Turn]) -> Action: ...


@dataclass
class RunResult:
    run_id: str
    status: RunStatus
    steps: list[StepRecord]
    log_dir: Path
    meta: dict = field(default_factory=dict)


def _content_hash(obs: Observation) -> str:
    """Hash of the page content and URL only. Focus moves on every click, but
    a user would not call a moved focus ring a change."""
    return hashlib.sha256(f"{obs.url_path}\n{obs.tree}".encode()).hexdigest()[:16]


def observation_hash(obs: Observation) -> str:
    """Hash of what the persona can see, without the step number or notes, so
    two steps with an unchanged page hash the same."""
    seen = json.dumps(
        {
            "tree": obs.tree,
            "focused": obs.focused and obs.focused.model_dump(),
            "url": obs.url_path,
        },
        sort_keys=True,
    )
    return hashlib.sha256(seen.encode()).hexdigest()[:16]


def run(
    page: Page,
    task: Task,
    persona: Persona,
    model: Model,
    log_root: Path,
    seed: int | None = None,
) -> RunResult:
    """Run one task to success, give-up or the step cap, logging every step.

    Writes `<log_root>/<run_id>/steps.jsonl` (one StepRecord per line, as each
    step happens) and `run.json` (what is needed to replay the run).
    """
    perturber = Perturber(persona.perturbation, seed=seed)
    policy = persona.action_policy
    page_name = urlparse(task.url).path.rsplit("/", 1)[-1]
    run_id = f"{datetime.now(UTC):%Y%m%dT%H%M%SZ}-{persona.id}-{uuid.uuid4().hex[:6]}"
    log_dir = log_root / run_id
    log_dir.mkdir(parents=True)

    meta = {
        "run_id": run_id,
        "persona": persona.id,
        "config_hash": persona.config_hash,
        "task": task.id,
        "page": page_name,
        "seed": perturber.seed,
        "model_id": model.model_id,
        "prompt_hash": getattr(model, "prompt_hash", None),
        "playwright": importlib.metadata.version("playwright"),
        "started_at": datetime.now(UTC).isoformat(),
    }
    steps: list[StepRecord] = []
    history: list[Turn] = []
    status: RunStatus = "crashed"
    notes: list[str] = []
    last_content: str | None = None

    try:
        page.goto(task.url)
        settle(page)
        with open(log_dir / "steps.jsonl", "a", encoding="utf-8") as log:
            for step in range(persona.memory.max_steps):
                obs, refs = observe(page, step, persona.perception.filters, notes)
                obs_hash = observation_hash(obs)
                content = _content_hash(obs)
                last = steps[-1] if steps else None
                if last and last.result == "ok" and content == last_content:
                    # A fact the persona would notice, except after a skipped
                    # field: a user who forgot a field expects no change, and
                    # the note would hint that the injected lapse happened.
                    if last.perturbation != SKIP_FIELD:
                        obs = obs.model_copy(
                            update={"persona_notes": [*notes, "Nothing visibly changed."]}
                        )

                window = persona.memory.history_turns
                action = model.next_action(task.text, obs, history[-window:] if window else [])

                if action.action == "give_up":
                    given_up = Perturbed(action)  # never perturbed, never executed
                    _write(
                        log,
                        steps,
                        _record(run_id, persona, page_name, step, obs_hash, action, given_up),
                    )
                    status = "gave_up"
                    break

                reason = validate(action, policy, refs)
                if reason:
                    perturbed = Perturbed(None, times=0)
                    result = "invalid"
                    notes = [f"That action was not possible: {reason}."]
                else:
                    perturbed = perturber.apply(action, refs)
                    result = _execute(page, perturbed, refs)
                    notes = ["That action did not work."] if result == "error" else []

                reached = goal_reached(page, task.goal.role, task.goal.name)
                record = _record(
                    run_id, persona, page_name, step, obs_hash, action, perturbed, result, reached
                )
                _write(log, steps, record)
                history.append(Turn(obs, action, result))
                last_content = content

                if reached:
                    status = "succeeded"
                    break
            else:
                status = "step_cap"
    finally:
        meta |= {
            "status": status,
            "steps": len(steps),
            "finished_at": datetime.now(UTC).isoformat(),
        }
        (log_dir / "run.json").write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")

    return RunResult(run_id, status, steps, log_dir, meta)


def _execute(page: Page, perturbed: Perturbed, refs: RefMap) -> Literal["ok", "error"]:
    action = perturbed.executed
    if perturbed.times == 0:
        return "ok"  # a skipped field: nothing reaches the browser
    if perturbed.times == 2:
        first = act(page, action, refs, settle_ms=0)
        act(page, action, refs, timeout_ms=SECOND_CLICK_TIMEOUT_MS, settle_ms=0)
        settle(page)
        return first
    return act(page, action, refs)


def _record(
    run_id: str,
    persona: Persona,
    page_name: str,
    step: int,
    obs_hash: str,
    intended: Action,
    perturbed: Perturbed,
    result: Literal["ok", "invalid", "error"] = "ok",
    goal_reached: bool = False,
) -> StepRecord:
    return StepRecord(
        run_id=run_id,
        persona=persona.id,
        page=page_name,
        step=step,
        observation_hash=obs_hash,
        intended_action=intended,
        executed_action=perturbed.executed,
        perturbation=perturbed.perturbation,
        result=result,
        goal_reached=goal_reached,
    )


def _write(log, steps: list[StepRecord], record: StepRecord) -> None:
    log.write(record.model_dump_json() + "\n")
    log.flush()  # the API streams this file while the run is going
    steps.append(record)
