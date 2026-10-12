import pytest
import yaml
from pydantic import ValidationError

from agent.actions import validate
from agent.contracts import Action
from agent.persona import PERSONAS_DIR, Persona, is_key_name, load_persona

P1_FILE = PERSONAS_DIR / "error_prone.yaml"


def p1_data():
    return yaml.safe_load(P1_FILE.read_text())


def write(tmp_path, data, name="error_prone"):
    path = tmp_path / f"{name}.yaml"
    path.write_text(yaml.safe_dump(data))
    return path


class TestP1Config:
    def test_matches_spec(self):
        p1 = load_persona("error_prone")
        assert p1.perception.filters == ["full_tree"]
        assert p1.actions.allowed == ["click", "type", "press", "back"]
        assert p1.actions.keys == ["Tab", "Enter", "Escape"]
        assert (p1.memory.history_turns, p1.memory.max_steps) == (3, 20)
        assert p1.perturbation.seed == 1234
        assert p1.perturbation.typo_rate == 0.15
        assert p1.perturbation.skip_field_rate == 0.10
        assert p1.perturbation.double_submit_rate == 0.10
        assert p1.perturbation.back_press_rate == 0.05
        assert p1.task_types == ["complete_form", "recover_from_error"]

    def test_load_by_path_equals_load_by_id(self):
        assert load_persona(P1_FILE) == load_persona("error_prone")

    def test_action_policy_feeds_the_validator(self):
        policy = load_persona("error_prone").action_policy
        assert validate(Action(thought="", action="scroll"), policy, {}) is not None
        assert validate(Action(thought="", action="press", key="Tab"), policy, {}) is None
        assert validate(Action(thought="", action="press", key="ArrowUp"), policy, {}) is not None


class TestRejected:
    @pytest.mark.parametrize(
        "change",
        [
            lambda d: d.update(mood="impatient"),  # unknown top-level key
            lambda d: d["memory"].update(patience=3),  # unknown nested key
            lambda d: d["actions"].update(allowed=["click", "hover"]),
            lambda d: d["actions"].update(allowed=["click", "give_up"]),
            lambda d: d["actions"].update(keys=["enter"]),
            lambda d: d["actions"].update(allowed=["click"]),  # keys without press
            lambda d: d["perception"].update(filters=["screenshot"]),  # no such filter
            lambda d: d["perception"].update(filters=[]),
            lambda d: d["perturbation"].update(typo_rate=1.5),
            lambda d: d["perturbation"].update(back_press_rate=-0.1),
            lambda d: d["memory"].update(history_turns=-1),
            lambda d: d["memory"].update(max_steps=0),
            lambda d: d.update(task_types=[]),
            lambda d: d.pop("memory"),
            # Strict types: YAML true would otherwise be a rate of 1.0.
            lambda d: d["perturbation"].update(typo_rate=True),
            lambda d: d["memory"].update(history_turns="3"),
            lambda d: d["memory"].update(max_steps=True),
            lambda d: d["perturbation"].update(seed="7"),
        ],
    )
    def test_invalid_config(self, tmp_path, change):
        data = p1_data()
        change(data)
        with pytest.raises(ValidationError):
            load_persona(write(tmp_path, data))

    def test_id_must_match_file_name(self, tmp_path):
        with pytest.raises(ValueError, match="does not match the file name"):
            load_persona(write(tmp_path, p1_data(), name="memoryless"))

    def test_not_a_mapping(self, tmp_path):
        path = tmp_path / "error_prone.yaml"
        path.write_text("- just\n- a list\n")
        with pytest.raises(ValueError, match="YAML mapping"):
            load_persona(path)

    @pytest.mark.parametrize("name", ["../secrets", "Error_Prone", ""])
    def test_bad_persona_id(self, name):
        with pytest.raises(ValueError, match="not a persona id"):
            load_persona(name)


class TestDefaults:
    def test_no_perturbation_section_means_none(self, tmp_path):
        # P2 and P3 change other axes and inject no mistakes.
        data = p1_data()
        del data["perturbation"]
        p = load_persona(write(tmp_path, data))
        assert p.perturbation.typo_rate == p.perturbation.double_submit_rate == 0.0


class TestKeyNames:
    @pytest.mark.parametrize(
        "key", ["Enter", "Tab", "a", "7", "F5", "KeyA", "Digit1", "Shift+Tab", "Control+a"]
    )
    def test_valid(self, key):
        assert is_key_name(key)

    @pytest.mark.parametrize(
        "key", ["enter", "tab", "Return", "Shift+", "Ctrl+a", "", "ab", "Keya"]
    )
    def test_invalid(self, key):
        assert not is_key_name(key)


class TestConfigHash:
    def test_stable_and_short(self):
        h = load_persona("error_prone").config_hash
        assert h == load_persona("error_prone").config_hash and len(h) == 16

    def test_ignores_comments_and_key_order(self, tmp_path):
        data = p1_data()
        reordered = dict(reversed(list(data.items())))
        path = tmp_path / "error_prone.yaml"
        path.write_text("# a comment\n" + yaml.safe_dump(reordered, sort_keys=False))
        assert load_persona(path).config_hash == load_persona("error_prone").config_hash

    def test_changes_when_a_limit_changes(self):
        p1 = load_persona("error_prone")
        data = p1.model_dump()
        data["perturbation"]["typo_rate"] = 0.2
        assert Persona.model_validate(data).config_hash != p1.config_hash


class TestP2AndP3Configs:
    """Spec, mid-eval scope: P2 and P3 are delivered as configs."""

    def test_p2_memoryless(self):
        p2 = load_persona("memoryless")
        assert p2.memory.history_turns == 0 and p2.memory.max_steps == 25
        assert p2.perception.filters == ["full_tree"]
        assert p2.perturbation.typo_rate == p2.perturbation.double_submit_rate == 0.0

    def test_p3_low_literacy(self):
        p3 = load_persona("low_literacy")
        assert p3.perception.filters == ["vocab_filter"] and p3.memory.max_steps == 15
        assert p3.perturbation.typo_rate == 0.0

    def test_personas_differ_on_one_axis_each(self):
        p1, p2, p3 = (load_persona(i) for i in ("error_prone", "memoryless", "low_literacy"))
        assert p1.perturbation.typo_rate > 0 == p2.perturbation.typo_rate  # P1: perturbation
        assert p2.memory.history_turns == 0 < p1.memory.history_turns  # P2: memory
        assert p3.perception.filters != p1.perception.filters  # P3: perception

    def test_unbuilt_filter_fails_loudly(self):
        from agent.perception import apply_filters

        with pytest.raises(NotImplementedError, match="not built yet"):
            apply_filters([], ["vocab_filter"])
