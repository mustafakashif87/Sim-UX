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
import random
import time
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal, Protocol
from urllib.parse import urlparse

from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import Page

from agent.actions import validate
from agent.behaviour import Escalation, Habit, World, klm_seconds, step_cap
from agent.browser import act, goal_reached, observe, settle
from agent.contracts import Action, Observation, StepRecord
from agent.environment import environment_page
from agent.ids import new_run_id
from agent.llm import ProviderError
from agent.perception import RefMap
from agent.persona import Persona
from agent.perturb import IMPATIENT_RETRY, SKIP_FIELD, Perturbed, Perturber, UnnoticedSlips
from agent.tasks import Goal, Task  # noqa: F401  (Goal re-exported for callers)

RunStatus = Literal["succeeded", "gave_up", "step_cap", "aborted_provider", "crashed"]

# The second click of a double submit comes straight after the first, as a
# real double press would. On a page that disables its button after one press
# the second click finds it disabled; that is the page working, not an error.
SECOND_CLICK_TIMEOUT_MS = 500


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
    condition: str = "persona",
    run_id: str | None = None,
) -> RunResult:
    """See `_run`. With an Environment (device, viewport, text scale) the run
    uses its own page in its own browser context, closed afterwards."""
    with environment_page(page, persona.environment) as own:
        return _run(own, task, persona, model, log_root, seed, condition, run_id)


def _run(
    page: Page,
    task: Task,
    persona: Persona,
    model: Model,
    log_root: Path,
    seed: int | None = None,
    condition: str = "persona",
    run_id: str | None = None,
) -> RunResult:
    """Run one task to success, give-up or the step cap, logging every step.
    A ProviderError from the model ends it as `aborted_provider`. `condition`
    is only logged: the caller passes the persona already set for it
    (`persona.for_condition`). `run_id` is made here unless given (the API
    makes it first so a client can follow the run at once).

    Writes to `<log_root>/<run_id>/`, each line as it happens:
    - `steps.jsonl`: one StepRecord per step
    - `observations.jsonl`: what the persona saw at each step, then the final
      page, each with the page's `<title>` (not shown to the persona)
    - `network.jsonl`: every non-GET request, with the step that caused it
    and at the end `run.json`, with what is needed to replay the run.
    Detectors read these files, never what the model said happened.
    """
    perturber = Perturber(persona.perturbation, seed=seed)
    policy = persona.action_policy
    page_name = urlparse(task.url).path.rsplit("/", 1)[-1]
    run_id = run_id or new_run_id(persona.id)
    log_dir = log_root / run_id
    log_dir.mkdir(parents=True)

    meta = {
        "run_id": run_id,
        "persona": persona.id,
        "condition": condition,
        "config_hash": persona.config_hash,
        "task": task.id,
        "critical_text": task.critical_text,
        "optimal_steps": task.optimal_steps,
        "page": page_name,
        "seed": perturber.seed,
        "model_id": model.model_id,
        "prompt_hash": getattr(model, "prompt_hash", None),
        "replay": getattr(model, "replay", False),
        "playwright": importlib.metadata.version("playwright"),
        "started_at": datetime.now(UTC).isoformat(),
    }
    steps: list[StepRecord] = []
    history: list[Turn] = []
    status: RunStatus = "crashed"
    notes: list[str] = []
    last_content: str | None = None
    current = {"step": -1}  # the step whose action is running; -1 while loading
    submissions: list[dict] = []

    def on_request(request) -> None:
        if request.method == "GET" or current["step"] < 0:
            return
        try:
            body = request.post_data
        except (PlaywrightError, UnicodeDecodeError):  # binary body
            body = None
        submissions.append(
            {"step": current["step"], "method": request.method, "url": request.url, "body": body}
        )

    page.on("request", on_request)
    server = Server(persona.environment.network, perturber.seed)
    # Its own stream, so P1 to P3 runs draw exactly as before.
    retry_rng = random.Random(f"impatient-{perturber.seed}")
    if task.endpoint:
        page.route(task.endpoint, server.answer)
        if persona.environment.network.latency_ms:
            server.watch(page)
    world = World(persona.environment)
    escalation = Escalation(persona.actions.escalation)
    habit = Habit(persona.memory.prior_knowledge)
    cap = step_cap(persona, task)
    meta["step_cap"] = cap
    slips = UnnoticedSlips()

    try:
        world.install_clock(page)
        page.goto(task.url)
        settle(page)
        with (
            open(log_dir / "steps.jsonl", "a", encoding="utf-8") as log,
            open(log_dir / "observations.jsonl", "a", encoding="utf-8") as obs_log,
            open(log_dir / "network.jsonl", "a", encoding="utf-8") as net_log,
        ):
            for step in range(cap):
                current["step"] = step
                if escalation.out_of_budget(step):
                    status = "step_cap"  # P11: the steps allowed after help ran out
                    break
                happened = world.before_step(page, step)
                if happened:
                    settle(page)
                if server.release_due():
                    # A held response arrived while the persona waited: the
                    # page may now show the goal with no further action.
                    settle(page)
                    if goal_reached(page, task.goal.role, task.goal.name):
                        status = "succeeded"
                        break
                evidence: dict | None = {} if persona.needs_evidence else None
                obs, refs = observe(
                    page, step, persona.perception.filters, notes, persona.perception, evidence
                )
                if evidence is not None:
                    evidence["network"] = server.state()
                    evidence |= happened or {}
                note = habit.note((evidence or {}).get("page", {}).get("viewport"))
                if note:
                    obs = obs.model_copy(update={"persona_notes": [*obs.persona_notes, note]})
                obs_hash = observation_hash(obs)
                content = _content_hash(obs)
                last = steps[-1] if steps else None
                escalation.update(content, obs.tree, last)
                if evidence is not None and escalation.config is not None:
                    evidence["help"] = escalation.evidence(refs)
                if last and last.result == "ok" and content == last_content:
                    # A fact the persona would notice, except after a skipped
                    # field: a user who forgot a field expects no change, and
                    # the note would hint that the injected lapse happened.
                    if last.perturbation != SKIP_FIELD:
                        obs = obs.model_copy(
                            update={"persona_notes": [*notes, "Nothing visibly changed."]}
                        )

                # The title is not in the tree the persona sees; it is logged for
                # detectors (lost_location: steps that share one title).
                entry = {"step": step, "observation": obs.model_dump(), "title": _title(page)}
                _append(obs_log, entry | (evidence or {}))

                window = persona.memory.history_turns
                if world.cold and persona.memory.reset_after_interruption:
                    window = 0  # back "cold" after an interruption (P9)
                seen = obs.model_copy(update={"tree": slips.shown(obs.tree, refs)})
                action = model.next_action(task.text, seen, history[-window:] if window else [])

                if action.action == "give_up":
                    given_up = Perturbed(action)  # never perturbed, never executed
                    _write(
                        log,
                        steps,
                        _record(run_id, persona, page_name, step, obs_hash, action, given_up),
                    )
                    status = "gave_up"
                    break

                focused_ref = obs.focused.ref if obs.focused else None
                reason = validate(action, policy, refs, focused_ref) or escalation.validate(
                    action, refs
                )
                if reason:
                    perturbed = Perturbed(None, times=0)
                    result = "invalid"
                    notes = [f"That action was not possible: {reason}."]
                else:
                    boxes = (evidence or {}).get("page", {}).get("boxes")
                    perturbed = perturber.apply(action, refs, boxes, habit.learned)
                    server.before_click()
                    result = _execute(page, perturbed, refs)
                    perturbed = _impatient_retry(page, perturbed, refs, server, retry_rng, persona)
                    notes = ["That action did not work."] if result == "error" else []
                    escalation.after(step, perturbed.executed, refs, result)
                    sent = any(sub["step"] == step for sub in submissions)
                    habit.learn(perturbed.executed, refs, boxes, sent)
                    slips.remember(perturbed, action, refs)
                    if sent:
                        slips.feedback()

                reached = goal_reached(page, task.goal.role, task.goal.name)
                for sub in submissions:
                    if sub["step"] == step:
                        _append(net_log, sub)
                record = _record(
                    run_id, persona, page_name, step, obs_hash, action, perturbed, result, reached
                )
                _write(log, steps, record)
                history.append(Turn(seen, action, result))
                last_content = content

                if reached:
                    status = "succeeded"
                    break
            else:
                status = "step_cap"
            # The page as the run left it: detectors compare it with the last
            # step. The run is already decided, so a page mid-navigation here
            # must not crash it; detectors cope with the entry missing.
            try:
                server.release_all()
                settle(page)
                evidence = {} if persona.needs_evidence else None
                final, _ = observe(
                    page, len(steps), persona.perception.filters, None, persona.perception, evidence
                )
                if evidence is not None:
                    evidence["network"] = server.state()
                entry = {
                    "step": len(steps),
                    "observation": final.model_dump(),
                    "title": _title(page),
                    "final": True,
                }
                _append(obs_log, entry | (evidence or {}))
            except PlaywrightError:
                pass
    except ProviderError as e:
        # The model could not answer (quota, bad key, unusable output). Not a
        # finding about the page: the run is excluded from k/5 and rerun.
        status = "aborted_provider"
        meta["error"] = str(e)
    finally:
        page.remove_listener("request", on_request)
        if task.endpoint:
            server.release_all()
            page.unroute(task.endpoint, server.answer)
        meta |= {
            "status": status,
            "steps": len(steps),
            "klm_seconds": klm_seconds(steps),
            "finished_at": datetime.now(UTC).isoformat(),
        }
        (log_dir / "run.json").write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")

    return RunResult(run_id, status, steps, log_dir, meta)


def _impatient_retry(page: Page, perturbed: Perturbed, refs: RefMap, server, rng, persona):
    """P10's slip: a click sent a request that is still waiting and the page
    shows no change, so the user presses again, at `impatient_retry_rate`.
    Applied after the click, because it depends on what the page did."""
    rate = persona.perturbation.impatient_retry_rate
    action = perturbed.executed
    if perturbed.times != 1 or action is None or action.action != "click":
        return perturbed
    if not server.waiting() or not server.unchanged_since_click(page):
        return perturbed
    server.silent_waits += 1  # evidence for no_loading_feedback, retry or not
    if not rate or rng.random() >= rate:
        return perturbed
    act(page, action, refs, timeout_ms=SECOND_CLICK_TIMEOUT_MS)
    return Perturbed(action, IMPATIENT_RETRY, times=2)


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


def _title(page: Page) -> str | None:
    try:
        return page.title()
    except PlaywrightError:
        return None


class Server:
    """Answers the task's submission endpoint as the Environment's network
    would: at once by default; after `latency_ms` (held, so the persona sees
    the page while it waits); or not at all, failing at `fail_rate` from a
    seeded draw. Held requests are answered at the start of the first step
    after they fall due, and all of them when the run ends."""

    def __init__(self, network, seed: int):
        self.latency_s = network.latency_ms / 1000
        self.fail_rate = network.fail_rate
        self._rng = random.Random(f"network-{seed}")
        self._held: list[tuple[float, object]] = []
        self.failed = 0
        self.sent = 0
        # Clicks after which a request waited and the page showed no change.
        self.silent_waits = 0
        self._tree_before_click: str | None = None
        self._page = None

    def answer(self, route) -> None:
        self.sent += 1
        if self.fail_rate and self._rng.random() < self.fail_rate:
            self.failed += 1
            route.abort("failed")
        elif self.latency_s:
            self._held.append((time.monotonic() + self.latency_s, route))
        else:
            _fulfill(route)

    def watch(self, page) -> None:
        """Remember the page, so the tree before each click can be kept."""
        self._page = page

    def before_click(self) -> None:
        if self._page is not None:
            self._tree_before_click = _tree_now(self._page)

    def waiting(self) -> bool:
        return bool(self._held)

    def unchanged_since_click(self, page) -> bool:
        """The page looks as it did before the click that sent the request."""
        before = self._tree_before_click
        return before is not None and _tree_now(page) == before

    def state(self) -> dict:
        """Logged with each observation for the P10 detectors."""
        return {
            "pending": len(self._held),
            "failed": self.failed,
            "sent": self.sent,
            "silent_waits": self.silent_waits,
        }

    def release_due(self) -> bool:
        """Answer every held request that has fallen due; True if any."""
        now = time.monotonic()
        due = [r for t, r in self._held if t <= now]
        self._held = [(t, r) for t, r in self._held if t > now]
        for route in due:
            _fulfill(route)
        return bool(due)

    def release_all(self) -> None:
        held, self._held = self._held, []
        for _, route in held:
            _fulfill(route)


def _tree_now(page) -> str | None:
    try:
        return page.locator("body").aria_snapshot(timeout=1000)
    except PlaywrightError:
        return None


def _fulfill(route) -> None:
    try:
        route.fulfill(status=200, body="ok", headers={"Access-Control-Allow-Origin": "*"})
    except PlaywrightError:  # the page went away while the request was held
        pass


def _append(log, entry: dict) -> None:
    log.write(json.dumps(entry) + "\n")
    log.flush()


def _write(log, steps: list[StepRecord], record: StepRecord) -> None:
    log.write(record.model_dump_json() + "\n")
    log.flush()  # the API streams this file while the run is going
    steps.append(record)
