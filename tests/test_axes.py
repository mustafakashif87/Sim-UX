"""Extension axes (persona catalogue, build steps 1 and 2): schema, the
geometry filters, and the new action rules. Pure: Views are built by hand."""

import pytest
from pydantic import ValidationError

from agent.actions import ActionPolicy, validate
from agent.contracts import Action
from agent.perception import (
    Box,
    RefTarget,
    View,
    apply_filters,
    assign_refs,
    parse_snapshot,
    render,
    walk,
)
from agent.persona import Persona, baseline, load_persona

TREE = """- heading "Shoes" [level=1]
- paragraph: Pick a size from the list below to see stock in your nearest shop today.
- button "Add to basket"
- contentinfo:
  - link "Terms\""""


def parsed():
    nodes = parse_snapshot(TREE)
    assign_refs(nodes)
    return nodes


def view_with(nodes, boxes, **kw):
    by_ref = {n.ref: n for n in walk(nodes) if n.ref}
    return View(
        viewport=Box(0, 0, 320, 256),
        boxes={id(by_ref[r]): Box(*b) for r, b in boxes.items()},
        **kw,
    )


class TestViewportOnly:
    def test_off_screen_nodes_are_dropped(self):
        nodes = parsed()
        # heading and paragraph on screen; button and footer below the fold
        view = view_with(
            nodes,
            {"e1": (0, 0, 300, 30), "e2": (0, 40, 300, 60), "e3": (0, 600, 100, 40),
             "e4": (0, 900, 320, 40), "e5": (0, 910, 50, 20)},
        )  # fmt: skip
        out = render(apply_filters(nodes, ["viewport_only"], view))
        assert "Shoes" in out and "Pick a size" in out
        assert "Add to basket" not in out and "Terms" not in out

    def test_needs_geometry(self):
        with pytest.raises(ValueError, match="needs page geometry"):
            apply_filters(parsed(), ["viewport_only"])


def test_skim_text_cuts_text_not_names():
    out = render(apply_filters(parsed(), ["skim_text"], View(Box(0, 0, 1, 1), skim_max_words=4)))
    assert "Pick a size from …" in out
    assert 'heading "Shoes"' in out and 'button "Add to basket"' in out


class TestLinearWindow:
    def test_window_from_the_top(self):
        nodes = parsed()
        view = view_with(nodes, {"e1": (0, 0, 300, 30)}, window_nodes=2)
        out = render(apply_filters(nodes, ["linear_window"], view))
        assert "Shoes" in out and "Pick a size" in out and "Add to basket" not in out

    def test_window_follows_focus_and_rotor_lists_headings(self):
        nodes = parsed()
        view = view_with(nodes, {}, window_nodes=2, focused_ref="e5", rotor=("headings",))
        out = render(apply_filters(nodes, ["linear_window"], view))
        assert 'heading "Shoes"' in out  # from the rotor
        assert "Terms" in out and "Pick a size" not in out


class TestActions:
    refs = {"e1": RefTarget("generic", None, 0, 0), "e2": RefTarget("button", "Go", 0, 0)}

    def test_interactive_roles_only(self):
        policy = ActionPolicy(frozenset({"click"}), frozenset(), interactive_roles_only=True)
        div = Action(thought="", action="click", ref="e1")
        assert "cannot be operated" in validate(div, policy, self.refs)
        assert validate(Action(thought="", action="click", ref="e2"), policy, self.refs) is None

    def test_type_focused_only(self):
        policy = ActionPolicy(frozenset({"type"}), frozenset(), type_focused_only=True)
        typing = Action(thought="", action="type", ref="e2", text="x")
        assert "has focus" in validate(typing, policy, self.refs, focused_ref="e1")
        assert validate(typing, policy, self.refs, focused_ref="e2") is None


class TestSchema:
    @pytest.mark.parametrize(
        "pid", ["screen_reader", "keyboard_only", "low_vision_zoom", "skimmer"]
    )
    def test_extension_configs_load_and_need_evidence(self, pid):
        p = load_persona(pid)
        assert p.needs_evidence
        b = baseline(p)
        assert b.perception.filters == ["full_tree"]
        assert not b.actions.interactive_roles_only and not b.actions.type_focused_only
        assert b.environment == p.environment  # the world stays the same

    def test_core_personas_log_no_extra_evidence(self):
        for pid in ("error_prone", "memoryless", "low_literacy"):
            assert not load_persona(pid).needs_evidence

    def test_unknown_device_rejected(self):
        data = load_persona("skimmer").model_dump()
        data["environment"]["device"] = "Nokia 3310"
        with pytest.raises(ValidationError, match="unknown device"):
            Persona.model_validate(data)
