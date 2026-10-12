"""Each detector fires on its buggy page and stays silent on the clean one
(spec: Evaluation protocol, Unit tests), through a full P1 run of the loop.

Fixture pairs differ only in the seeded bug; which file is buggy is recorded
here, not in the file name:
  signup-a.html buggy, signup-b.html clean  (B1, data_loss_on_error)
  order-a.html  buggy, order-b.html  clean  (B4, duplicate_submission)
"""

from pathlib import Path

import pytest

from agent.detectors import detect, load_run
from agent.fake_model import FakeModel, click, type_into
from agent.loop import Goal, Task, run
from agent.persona import Persona, load_persona

PAGES = Path(__file__).parents[1] / "fixtures" / "pages"


def task(page, goal, endpoint):
    return Task(
        id=page,
        url=(PAGES / page).resolve().as_uri(),
        text="Complete the form",
        goal=Goal("heading", goal),
        endpoint=endpoint,
    )


def p1(**rates):
    """P1 with only the given perturbations on, so each test injects one mistake."""
    data = load_persona("error_prone").model_dump()
    data["perturbation"] = {"seed": 1, **rates}
    return Persona.model_validate(data)


def signals(browser, tmp_path, page_task, persona, script):
    page = browser.new_page()
    try:
        result = run(page, page_task, persona, FakeModel(script), tmp_path)
    finally:
        page.close()
    return [f.signal for f in detect(load_run(result.log_dir))], result


SIGN_UP = ["signup-a.html", "signup-b.html"]
ORDER = ["order-a.html", "order-b.html"]


class TestB1DataLoss:
    # The persona mistypes the email (as P1's typo does), then submits.
    script = [
        type_into("Full name", "Sara Khan"),
        type_into("Email", "sara.example.com"),
        click("Create account"),
    ]

    @pytest.mark.parametrize("page, fires", [(SIGN_UP[0], True), (SIGN_UP[1], False)])
    def test_fires_on_buggy_only(self, browser, tmp_path, page, fires):
        t = task(page, "Account created", "**/api/signup")
        found, _ = signals(browser, tmp_path, t, p1(), self.script)
        assert ("data_loss_on_error" in found) == fires

    @pytest.mark.parametrize("page", SIGN_UP)
    def test_silent_when_no_error(self, browser, tmp_path, page):
        script = [type_into("Full name", "Sara Khan"), type_into("Email", "sara@example.com")]
        t = task(page, "Account created", "**/api/signup")
        found, result = signals(browser, tmp_path, t, p1(), [*script, click("Create account")])
        assert found == [] and result.status == "succeeded"


class TestB4DuplicateSubmission:
    @pytest.mark.parametrize("page, fires", [(ORDER[0], True), (ORDER[1], False)])
    def test_double_submit_fires_on_buggy_only(self, browser, tmp_path, page, fires):
        t = task(page, "Order placed", "**/api/orders")
        persona = p1(double_submit_rate=1.0)
        found, result = signals(browser, tmp_path, t, persona, [click("Place order")])
        assert ("duplicate_submission" in found) == fires
        assert result.status == "succeeded"

    @pytest.mark.parametrize("page", ORDER)
    def test_single_press_is_silent(self, browser, tmp_path, page):
        t = task(page, "Order placed", "**/api/orders")
        found, _ = signals(browser, tmp_path, t, p1(), [click("Place order")])
        assert found == []


def test_logs_hold_the_evidence(browser, tmp_path):
    t = task(ORDER[0], "Order placed", "**/api/orders")
    _, result = signals(browser, tmp_path, t, p1(double_submit_rate=1.0), [click("Place order")])
    log = load_run(result.log_dir)
    assert [s.step for s in log.submissions] == [0, 0]
    assert len(log.observations) == len(log.steps) + 1  # plus the final page
