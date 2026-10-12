import random
from collections import Counter

import pytest
from pydantic import ValidationError

from agent.contracts import Action, StepRecord
from agent.perception import RefTarget
from agent.persona import Perturbation, load_persona
from agent.perturb import (
    BACK_PRESS,
    DOUBLE_SUBMIT,
    SKIP_FIELD,
    TYPO,
    Perturbed,
    Perturber,
    swap_adjacent,
)

REFS = {
    "e1": RefTarget(role="textbox", name="Email", nth=0, nth_in_role=0),
    "e2": RefTarget(role="button", name="Place order", nth=0, nth_in_role=0),
    "e3": RefTarget(role="link", name="Help", nth=0, nth_in_role=0),
    "e4": RefTarget(role="checkbox", name="I agree", nth=0, nth_in_role=0),
}
TYPE = Action(thought="enter email", action="type", ref="e1", text="sara@example.com")
SUBMIT = Action(thought="submit", action="click", ref="e2")
LINK = Action(thought="help", action="click", ref="e3")
CHECK = Action(thought="agree", action="click", ref="e4")
TAB = Action(thought="next", action="press", key="Tab")
BACK = Action(thought="go back", action="back")
GIVE_UP = Action(thought="stuck", action="give_up")

P1 = load_persona("error_prone").perturbation
NONE = Perturbation()
N = 20_000


def counts(perturber, action):
    return Counter(perturber.apply(action, REFS).perturbation for _ in range(N))


class TestRates:
    """Spec, Unit tests: each perturbation fires at its configured rate for a fixed seed."""

    @pytest.mark.parametrize(
        "action, expected",
        [
            (TYPE, {BACK_PRESS: 0.05, SKIP_FIELD: 0.10, TYPO: 0.15}),
            (SUBMIT, {BACK_PRESS: 0.05, DOUBLE_SUBMIT: 0.10}),
            (TAB, {BACK_PRESS: 0.05}),
        ],
    )
    def test_p1_rates(self, action, expected):
        seen = counts(Perturber(P1, seed=1), action)
        for name, rate in expected.items():
            # 4 standard deviations at N=20,000 is under 0.011 for these rates.
            assert seen[name] / N == pytest.approx(rate, abs=0.011), name
        assert set(seen) <= set(expected) | {None}

    def test_zero_rates_never_perturb(self):
        p = Perturber(NONE, seed=1)
        for action in (TYPE, SUBMIT, LINK, TAB, BACK):
            assert counts(p, action) == Counter({None: N})

    def test_rate_one_always_fires(self):
        p = Perturber(Perturbation(double_submit_rate=1.0), seed=1)
        assert counts(p, SUBMIT) == Counter({DOUBLE_SUBMIT: N})


class TestDeterminism:
    def run(self, seed):
        p = Perturber(P1, seed=seed)
        return [p.apply(a, REFS) for a in [TYPE, SUBMIT, TAB] * 200]

    def test_same_seed_same_mistakes(self):
        assert self.run(seed=3) == self.run(seed=3)

    def test_different_seed_different_mistakes(self):
        assert self.run(seed=3) != self.run(seed=4)

    def test_config_seed_used_by_default(self):
        assert Perturber(P1).seed == 1234
        assert Perturber(P1, seed=5).seed == 5


class TestEachMistake:
    def test_typo_swaps_two_adjacent_characters(self):
        out = Perturber(Perturbation(typo_rate=1.0), seed=1).apply(TYPE, REFS)
        assert out.perturbation == TYPO and out.times == 1
        typed, meant = out.executed.text, TYPE.text
        diff = [i for i in range(len(meant)) if typed[i] != meant[i]]
        assert len(diff) == 2 and diff[1] == diff[0] + 1
        assert sorted(typed) == sorted(meant)
        assert out.executed.ref == TYPE.ref

    @pytest.mark.parametrize("text", ["", "a", "aaa"])
    def test_typo_with_nothing_to_swap_is_no_mistake(self, text):
        action = TYPE.model_copy(update={"text": text})
        out = Perturber(Perturbation(typo_rate=1.0), seed=1).apply(action, REFS)
        assert out == Perturbed(action)

    def test_skip_field_drops_the_action(self):
        out = Perturber(Perturbation(skip_field_rate=1.0), seed=1).apply(TYPE, REFS)
        assert (out.executed, out.perturbation, out.times) == (None, SKIP_FIELD, 0)

    def test_double_submit_executes_the_click_twice(self):
        out = Perturber(Perturbation(double_submit_rate=1.0), seed=1).apply(SUBMIT, REFS)
        assert (out.executed, out.perturbation, out.times) == (SUBMIT, DOUBLE_SUBMIT, 2)

    @pytest.mark.parametrize("action", [LINK, CHECK, TYPE, TAB])
    def test_double_submit_only_on_buttons(self, action):
        # A second click on a checkbox would undo it: a model failure, not a page bug.
        p = Perturber(Perturbation(double_submit_rate=1.0), seed=1)
        assert p.apply(action, REFS).perturbation is None

    def test_back_press_replaces_the_action(self):
        out = Perturber(Perturbation(back_press_rate=1.0), seed=1).apply(SUBMIT, REFS)
        assert out.perturbation == BACK_PRESS
        assert out.executed.action == "back" and out.executed.ref is None

    def test_back_press_not_injected_on_back(self):
        p = Perturber(Perturbation(back_press_rate=1.0), seed=1)
        assert p.apply(BACK, REFS).perturbation is None

    @pytest.mark.parametrize("config", [P1, Perturbation(back_press_rate=1.0)])
    def test_give_up_is_never_perturbed(self, config):
        assert Perturber(config, seed=1).apply(GIVE_UP, REFS).executed == GIVE_UP


class TestStepRecord:
    def test_result_fits_the_step_record(self):
        out = Perturber(Perturbation(typo_rate=1.0), seed=1).apply(TYPE, REFS)
        record = StepRecord(
            run_id="r1",
            persona="error_prone",
            page="signup-a.html",
            step=0,
            observation_hash="abc",
            intended_action=TYPE,
            executed_action=out.executed,
            perturbation=out.perturbation,
            result="ok",
            goal_reached=False,
        )
        assert record.intended_action.text != record.executed_action.text


class TestConfig:
    @pytest.mark.parametrize(
        "rates",
        [
            {"back_press_rate": 0.5, "skip_field_rate": 0.3, "typo_rate": 0.3},
            {"back_press_rate": 0.6, "double_submit_rate": 0.5},
        ],
    )
    def test_rates_for_one_action_cannot_exceed_one(self, rates):
        with pytest.raises(ValidationError, match="more than 1"):
            Perturbation(**rates)

    def test_rates_adding_up_to_exactly_one_allowed(self):
        p = Perturbation(back_press_rate=0.33, skip_field_rate=0.56, typo_rate=0.11)
        assert p.back_press_rate + p.skip_field_rate + p.typo_rate > 1.0  # float rounding


def test_swap_adjacent():
    assert swap_adjacent("ab", random.Random(0)) == "ba"
    assert swap_adjacent("aab", random.Random(0)) == "aba"
    assert swap_adjacent("aa", random.Random(0)) == "aa"
