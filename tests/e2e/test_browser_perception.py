from agent.browser import locate, observe
from agent.perception import FILTERS


def ref_for(refs, role, name, nth=0):
    matches = [r for r, t in refs.items() if (t.role, t.name) == (role, name)]
    return matches[nth]


def element_id(page, refs, ref):
    return locate(page, refs[ref]).evaluate("el => el.id")


def test_observation_has_refs_and_no_html(open_fixture):
    page = open_fixture("perception.html")
    obs, refs = observe(page, step=0, filters=["full_tree"])
    assert obs.step == 0 and obs.url_path.endswith("perception.html")
    assert obs.tree.count("[ref=") == len(refs) == 14
    assert "<" not in obs.tree and "id=" not in obs.tree
    assert obs.focused is None


def test_every_ref_resolves_to_exactly_one_element(open_fixture):
    page = open_fixture("perception.html")
    _, refs = observe(page, step=0, filters=["full_tree"])
    for ref, target in refs.items():
        assert locate(page, target).count() == 1, ref


def test_duplicate_and_unnamed_refs_hit_the_right_element(open_fixture):
    page = open_fixture("perception.html")
    _, refs = observe(page, step=0, filters=["full_tree"])
    assert element_id(page, refs, ref_for(refs, "button", "Save", 0)) == "save-1"
    assert element_id(page, refs, ref_for(refs, "button", "Save", 1)) == "save-2"
    assert element_id(page, refs, ref_for(refs, "button", None)) == "icon"
    assert element_id(page, refs, ref_for(refs, "textbox", "Email address")) == "email"


def test_focused_element_reported_by_ref(open_fixture):
    page = open_fixture("perception.html")
    page.locator("#save-2").focus()
    obs, refs = observe(page, step=1, filters=["full_tree"])
    assert obs.focused is not None
    assert obs.focused.ref == ref_for(refs, "button", "Save", 1)
    assert (obs.focused.role, obs.focused.name) == ("button", "Save")


def test_filtered_out_elements_cannot_be_targeted(open_fixture, monkeypatch):
    def drop_buttons(nodes):
        for n in nodes:
            n.children = [c for c in n.children if c.role != "button"]
        return nodes

    monkeypatch.setitem(FILTERS, "no_buttons", drop_buttons)
    page = open_fixture("perception.html")
    obs, refs = observe(page, step=0, filters=["no_buttons"])
    assert "button" not in obs.tree
    assert all(t.role != "button" for t in refs.values())
    # Positions are still counted on the full page, so other refs stay correct.
    assert element_id(page, refs, ref_for(refs, "textbox", "Email address")) == "email"


def test_persona_notes_passed_through(open_fixture):
    page = open_fixture("perception.html")
    notes = ["your last submit changed nothing"]
    obs, _ = observe(page, step=2, filters=["full_tree"], notes=notes)
    assert obs.persona_notes == notes
