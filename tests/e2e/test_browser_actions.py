import pytest

from agent.browser import act, observe
from agent.contracts import Action


def ref_for(refs, role, name):
    return next(r for r, t in refs.items() if (t.role, t.name) == (role, name))


def text_of(page, selector):
    return page.locator(selector).text_content()


@pytest.fixture
def page_and_refs(open_fixture):
    page = open_fixture("actions.html")
    _, refs = observe(page, step=0, filters=["full_tree"])
    return page, refs


def test_click(page_and_refs):
    page, refs = page_and_refs
    action = Action(thought="", action="click", ref=ref_for(refs, "button", "Add"))
    assert act(page, action, refs) == "ok"
    assert text_of(page, "#count") == "1"


def test_type_replaces_value(page_and_refs):
    page, refs = page_and_refs
    ref = ref_for(refs, "textbox", "Full name")
    action = Action(thought="", action="type", ref=ref, text="Ali")
    assert act(page, action, refs) == "ok"
    assert page.locator("#name").input_value() == "Ali"


def test_press_goes_to_focus_without_ref(page_and_refs):
    page, refs = page_and_refs
    page.locator("#add").focus()
    assert act(page, Action(thought="", action="press", key="Enter"), refs) == "ok"
    assert text_of(page, "#count") == "1"


def test_press_on_ref(page_and_refs):
    page, refs = page_and_refs
    action = Action(
        thought="", action="press", ref=ref_for(refs, "textbox", "Full name"), key="Escape"
    )
    assert act(page, action, refs) == "ok"
    assert text_of(page, "#last-key") == "Escape"


def test_scroll_brings_ref_into_view(page_and_refs):
    page, refs = page_and_refs
    far = page.locator("#far")
    assert not far.evaluate("el => el.getBoundingClientRect().top < window.innerHeight")
    action = Action(thought="", action="scroll", ref=ref_for(refs, "button", "Far away"))
    assert act(page, action, refs) == "ok"
    assert far.evaluate("el => el.getBoundingClientRect().top < window.innerHeight")


def test_scroll_without_ref_moves_page(page_and_refs):
    page, refs = page_and_refs
    assert act(page, Action(thought="", action="scroll"), refs) == "ok"
    page.wait_for_function("() => window.scrollY > 0")


def test_navigation_has_finished_when_act_returns(page_and_refs):
    page, refs = page_and_refs
    act(page, Action(thought="", action="click", ref=ref_for(refs, "link", "Next page")), refs)
    assert page.url.endswith("perception.html")
    assert page.get_by_role("heading", name="Sign up").count() == 1


def test_fetch_result_is_on_the_page_when_act_returns(page_and_refs):
    page, refs = page_and_refs
    page.route(
        "https://fixture.test/api/send",
        lambda route: route.fulfill(body="Sent", headers={"Access-Control-Allow-Origin": "*"}),
    )
    act(page, Action(thought="", action="click", ref=ref_for(refs, "button", "Send")), refs)
    assert text_of(page, "#sent") == "Sent"


def test_back_returns_to_previous_page(page_and_refs):
    page, refs = page_and_refs
    act(page, Action(thought="", action="click", ref=ref_for(refs, "link", "Next page")), refs)
    assert act(page, Action(thought="", action="back"), refs) == "ok"
    assert page.url.endswith("actions.html")


def test_back_with_no_history_is_an_error(page_and_refs):
    page, refs = page_and_refs
    assert act(page, Action(thought="", action="back"), refs) == "error"
    assert page.url.endswith("actions.html")


def test_browser_failure_returns_error_not_exception(page_and_refs):
    page, refs = page_and_refs
    action = Action(thought="", action="click", ref=ref_for(refs, "button", "Locked"))
    assert act(page, action, refs, timeout_ms=300) == "error"


def test_ref_missing_from_map_is_an_error_not_a_crash(page_and_refs):
    page, refs = page_and_refs
    assert act(page, Action(thought="", action="click", ref="e999"), refs) == "error"
    assert text_of(page, "#count") == "0"


def test_give_up_is_never_executed(page_and_refs):
    page, refs = page_and_refs
    with pytest.raises(ValueError, match="ends the run"):
        act(page, Action(thought="", action="give_up"), refs)
