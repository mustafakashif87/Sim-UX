import json
from pathlib import Path

import pytest

from agent.contracts import Action, StepRecord
from agent.fake_model import FakeModel, back, click, give_up, literal, press, type_into
from agent.llm import ProviderError
from agent.loop import Goal, Task, run
from agent.persona import Persona, load_persona

FIXTURE_PAGES = Path(__file__).parents[1] / "fixtures" / "pages"

TASK = Task(
    id="contact",
    url=(FIXTURE_PAGES / "loop.html").resolve().as_uri(),
    text="Send a message as Sara Khan",
    goal=Goal(role="heading", name="Message sent"),
)
SEND = [type_into("Full name", "Sara Khan"), click("Send")]


def persona(perturbation=None, **memory):
    """P1 with its perturbation off unless a test turns one on."""
    data = load_persona("error_prone").model_dump()
    data["perturbation"] = {"seed": 1, **(perturbation or {})}
    data["memory"].update(memory)
    return Persona.model_validate(data)


@pytest.fixture
def page(browser):
    """A fresh page whose form endpoint is intercepted; `page.posts` counts submissions."""
    page = browser.new_page()
    page.posts = []

    def handle(route):
        page.posts.append(route.request.post_data)
        route.fulfill(body="ok", headers={"Access-Control-Allow-Origin": "*"})

    page.route("https://fixture.test/api/send", handle)
    yield page
    page.close()


def go(page, tmp_path, script, p=None, seed=None):
    model = FakeModel(script)
    return run(page, TASK, p or persona(), model, tmp_path, seed=seed), model


class TestEnding:
    def test_goal_reached_ends_the_run(self, page, tmp_path):
        result, _ = go(page, tmp_path, SEND + [click("Refresh")])
        assert result.status == "succeeded"
        assert len(result.steps) == 2  # the extra scripted step never ran
        assert [s.goal_reached for s in result.steps] == [False, True]

    def test_step_cap(self, page, tmp_path):
        result, _ = go(page, tmp_path, [press("Tab")] * 10, persona(max_steps=3))
        assert result.status == "step_cap" and len(result.steps) == 3

    def test_give_up(self, page, tmp_path):
        result, _ = go(page, tmp_path, [give_up()])
        assert result.status == "gave_up"
        (step,) = result.steps
        assert step.intended_action.action == "give_up" == step.executed_action.action

    def test_model_cannot_declare_success(self, page, tmp_path):
        # Giving up on a page where the goal is not met is all the model can do.
        result, _ = go(page, tmp_path, [type_into("Full name", "Sara Khan")])
        assert result.status == "gave_up"
        assert not any(s.goal_reached for s in result.steps)

    def test_crash_is_logged_and_raised(self, page, tmp_path):
        def boom(obs):
            raise RuntimeError("model failed")

        with pytest.raises(RuntimeError):
            go(page, tmp_path, [boom])
        (run_json,) = tmp_path.glob("*/run.json")
        assert json.loads(run_json.read_text())["status"] == "crashed"

    def test_provider_failure_aborts_without_crashing(self, page, tmp_path):
        def quota_spent(obs):
            raise ProviderError("HTTP 429: quota spent")

        result, _ = go(page, tmp_path, [type_into("Full name", "Sara Khan"), quota_spent])
        assert result.status == "aborted_provider" and len(result.steps) == 1
        meta = json.loads((result.log_dir / "run.json").read_text())
        assert meta["status"] == "aborted_provider" and "quota" in meta["error"]


class TestValidation:
    def test_unknown_ref_is_invalid_and_the_persona_is_told(self, page, tmp_path):
        result, model = go(
            page, tmp_path, [literal(Action(thought="", action="click", ref="e999"))] + SEND
        )
        first = result.steps[0]
        assert (first.result, first.executed_action) == ("invalid", None)
        assert "not possible" in model.seen[1][0].persona_notes[0]
        assert result.status == "succeeded"

    def test_action_outside_whitelist_is_invalid(self, page, tmp_path):
        result, _ = go(page, tmp_path, [literal(Action(thought="", action="scroll"))])
        assert result.steps[0].result == "invalid"


class TestPerturbation:
    def test_typo_reaches_the_page_and_both_actions_are_logged(self, page, tmp_path):
        result, _ = go(page, tmp_path, SEND, persona({"typo_rate": 1.0}))
        typed = result.steps[0]
        assert typed.perturbation == "typo"
        assert typed.executed_action.text != typed.intended_action.text == "Sara Khan"
        assert page.posts == [typed.executed_action.text]

    def test_skipped_field_leaves_it_empty(self, page, tmp_path):
        result, _ = go(page, tmp_path, SEND, persona({"skip_field_rate": 1.0}))
        skipped = result.steps[0]
        assert (skipped.perturbation, skipped.executed_action) == ("skip_field", None)
        assert page.locator("#name").input_value() == ""
        assert page.posts == [] and result.status == "gave_up"

    def test_double_submit_sends_twice_on_a_button_that_stays_enabled(self, page, tmp_path):
        result, _ = go(page, tmp_path, SEND, persona({"double_submit_rate": 1.0}))
        assert result.steps[1].perturbation == "double_submit"
        assert len(page.posts) == 2 and result.status == "succeeded"

    def test_double_submit_sends_once_on_a_button_that_disables(self, page, tmp_path):
        script = [type_into("Full name", "Sara Khan"), click("Send once")]
        result, _ = go(page, tmp_path, script, persona({"double_submit_rate": 1.0}))
        assert result.steps[1].perturbation == "double_submit"
        assert result.steps[1].result == "ok"  # the blocked second press is not an error
        assert len(page.posts) == 1

    def test_back_press(self, page, tmp_path):
        result, _ = go(page, tmp_path, [click("Help", role="link"), back()], persona())
        assert result.steps[1].result == "ok"
        assert page.url.endswith("loop.html")

    def test_same_seed_same_run(self, browser, tmp_path):
        p = load_persona("error_prone")
        script = [type_into("Full name", "Sara Khan"), press("Tab"), click("Refresh")] * 3

        def mistakes(seed):
            page = browser.new_page()
            try:
                result, _ = go(page, tmp_path, script, p, seed=seed)
            finally:
                page.close()
            return [(s.intended_action, s.executed_action, s.perturbation) for s in result.steps]

        assert mistakes(seed=2) == mistakes(seed=2)


class TestWhatThePersonaSees:
    @pytest.mark.parametrize("turns", [0, 1, 3])
    def test_history_window(self, page, tmp_path, turns):
        result, model = go(page, tmp_path, [press("Tab")] * 6, persona(history_turns=turns))
        sizes = [len(history) for _, history in model.seen]
        assert sizes == [min(i, turns) for i in range(len(model.seen))]

    def test_nothing_changed_is_noticed(self, page, tmp_path):
        _, model = go(page, tmp_path, [click("Refresh"), give_up()])
        assert "Nothing visibly changed." in model.seen[1][0].persona_notes

    def test_skipped_field_is_not_hinted(self, page, tmp_path):
        p = persona({"skip_field_rate": 1.0})
        _, model = go(page, tmp_path, [type_into("Full name", "Sara Khan"), give_up()], p)
        assert model.seen[1][0].persona_notes == []


class TestLog:
    def test_steps_and_run_file(self, page, tmp_path):
        result, _ = go(page, tmp_path, SEND)
        lines = (result.log_dir / "steps.jsonl").read_text().splitlines()
        assert [StepRecord.model_validate_json(line) for line in lines] == result.steps
        meta = json.loads((result.log_dir / "run.json").read_text())
        assert meta["status"] == "succeeded" and meta["steps"] == 2
        assert meta["config_hash"] == persona().config_hash
        assert meta["model_id"] == "fake" and meta["seed"] == 1
        assert meta["page"] == "loop.html" and meta["playwright"]
        assert all(s.run_id == result.run_id for s in result.steps)

    def test_observation_hash_includes_focus(self, page, tmp_path):
        result, _ = go(page, tmp_path, [click("Refresh"), click("Refresh"), press("Tab")])
        hashes = [s.observation_hash for s in result.steps]
        assert hashes[0] != hashes[1]  # focus moved onto Refresh
        assert hashes[1] == hashes[2]  # nothing else changed
