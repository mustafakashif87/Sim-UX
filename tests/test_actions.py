import pytest

from agent.actions import ActionPolicy, validate
from agent.contracts import Action
from agent.perception import RefTarget

# The P1 Error-prone user's action axis (spec: Config schema).
P1 = ActionPolicy(
    allowed=frozenset({"click", "type", "press", "back"}),
    keys=frozenset({"Tab", "Enter", "Escape"}),
)

REFS = {
    "e1": RefTarget(role="textbox", name="Full name", nth=0, nth_in_role=0),
    "e2": RefTarget(role="button", name="Save", nth=0, nth_in_role=0),
}


def act(**kwargs):
    return Action(thought="", **kwargs)


class TestValidate:
    @pytest.mark.parametrize(
        "action",
        [
            act(action="click", ref="e2"),
            act(action="type", ref="e1", text="Ali"),
            act(action="press", key="Tab"),
            act(action="press", ref="e1", key="Enter"),
            act(action="back"),
        ],
    )
    def test_allowed_actions_pass(self, action):
        assert validate(action, P1, REFS) is None

    def test_action_outside_whitelist_rejected(self):
        reason = validate(act(action="scroll"), P1, REFS)
        assert reason == "action 'scroll' is not available"

    def test_give_up_always_allowed(self):
        nothing = ActionPolicy(allowed=frozenset(), keys=frozenset())
        assert validate(act(action="give_up"), nothing, {}) is None

    def test_unknown_ref_rejected(self):
        assert validate(act(action="click", ref="e9"), P1, REFS) == "no element e9 on this page"

    def test_filtered_out_ref_rejected(self):
        # A ref the persona's filter removed is absent from its RefMap.
        visible = {"e1": REFS["e1"]}
        assert validate(act(action="click", ref="e2"), P1, visible) is not None

    def test_ref_checked_on_press_too(self):
        assert validate(act(action="press", ref="e9", key="Enter"), P1, REFS) is not None

    def test_key_outside_whitelist_rejected(self):
        reason = validate(act(action="press", key="ArrowDown"), P1, REFS)
        assert reason == "key 'ArrowDown' is not available"

    def test_keyboard_only_persona_is_one_config_line(self):
        keyboard = ActionPolicy(allowed=frozenset({"press"}), keys=P1.keys)
        assert validate(act(action="click", ref="e2"), keyboard, REFS) is not None
        assert validate(act(action="press", key="Tab"), keyboard, REFS) is None

    def test_reasons_never_leak_locators(self):
        reason = validate(act(action="click", ref="e9"), P1, REFS)
        assert "button" not in reason and "Save" not in reason


class TestPolicy:
    def test_unknown_action_rejected(self):
        with pytest.raises(ValueError, match="unknown actions"):
            ActionPolicy(allowed=frozenset({"click", "hover"}), keys=frozenset())

    def test_give_up_is_not_a_policy_action(self):
        with pytest.raises(ValueError, match="give_up"):
            ActionPolicy(allowed=frozenset({"give_up"}), keys=frozenset())
