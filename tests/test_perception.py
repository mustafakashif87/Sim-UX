from pathlib import Path

import pytest

from agent.perception import (
    RefTarget,
    SnapshotError,
    apply_filters,
    assign_refs,
    parse_snapshot,
    render,
)

# Captured from Chromium for tests/fixtures/pages/perception.html.
SNAPSHOT = (Path(__file__).parent / "fixtures/snapshots/perception.yaml").read_text()


@pytest.fixture
def nodes():
    return parse_snapshot(SNAPSHOT)


def flat(nodes):
    for n in nodes:
        yield n
        yield from flat(n.children)


class TestParse:
    def test_roles_names_and_nesting(self, nodes):
        nav, main = nodes
        assert (nav.role, nav.name) == ("navigation", "Site")
        assert nav.children[0].role == "link"
        assert main.role == "main" and main.name is None

    def test_inline_text_attrs_and_props(self, nodes):
        by_name = {n.name: n for n in flat(nodes) if n.name}
        assert by_name["Full name"].text == "Ali"
        assert by_name["Sign up"].attrs == {"level": "1"}
        assert by_name["Free"].attrs == {"selected": ""}
        assert by_name["All pages"].props == {"url": "other.html"}

    def test_text_nodes_kept(self, nodes):
        texts = [n.text for n in flat(nodes) if n.role == "text"]
        assert "Email address" in texts

    def test_yaml_quoted_names(self):
        snap = """- main:
  - 'button "Save: now"'
  - button "He said \\"hi\\""
  - textbox "Ünïcode": "a: b"
"""
        names = [n.name for n in flat(parse_snapshot(snap))]
        assert names == [None, "Save: now", 'He said "hi"', "Ünïcode"]

    @pytest.mark.parametrize("bad", ["- <div>", "just a string", "- Button"])
    def test_unrecognised_input_rejected(self, bad):
        with pytest.raises(SnapshotError):
            parse_snapshot(bad)

    def test_empty_snapshot(self):
        assert parse_snapshot("") == []


class TestRefs:
    def test_every_element_gets_a_ref_text_does_not(self, nodes):
        refs = assign_refs(nodes)
        for n in flat(nodes):
            assert (n.ref is None) == (n.role == "text")
        assert list(refs) == [f"e{i}" for i in range(1, len(refs) + 1)]

    def test_duplicate_names_are_distinguished(self, nodes):
        refs = assign_refs(nodes)
        saves = [t for t in refs.values() if t.name == "Save"]
        assert [t.nth for t in saves] == [0, 1]

    def test_unnamed_element_uses_position_in_role(self, nodes):
        refs = assign_refs(nodes)
        unnamed = [t for t in refs.values() if t.role == "button" and t.name is None]
        assert unnamed == [RefTarget(role="button", name=None, nth=0, nth_in_role=2)]


class TestRender:
    def test_refs_shown_and_no_html(self, nodes):
        refs = assign_refs(nodes)
        out = render(nodes)
        assert '- button "Save" [ref=e' in out
        assert '- textbox "Full name" [ref=e' in out and out.count("[ref=") == len(refs) == 14
        assert "<" not in out and ">" not in out

    def test_structure_survives_render(self, nodes):
        assign_refs(nodes)
        out = render(nodes)
        assert "  - /url: other.html" in out
        assert '    - option "Free" [selected] [ref=' in out
        assert "  - text: Full name" in out


class TestFilters:
    def test_full_tree_is_identity(self, nodes):
        assert apply_filters(nodes, ["full_tree"]) is nodes

    def test_unknown_filter_rejected(self, nodes):
        with pytest.raises(ValueError, match="unknown perception filter"):
            apply_filters(nodes, ["viewport_only"])
