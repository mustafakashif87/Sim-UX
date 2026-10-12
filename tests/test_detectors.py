"""Detectors on hand-built run logs: no browser, so edge cases are cheap."""

import pytest

from agent.contracts import Action, Observation, StepRecord
from agent.detectors import RunLog, Submission, detect, signal_map
from agent.detectors.data_loss import data_loss_on_error, lost_fields
from agent.detectors.duplicate_submission import duplicate_submission

SUBMIT = Action(thought="", action="click", ref="e9")
TYPE = Action(thought="", action="type", ref="e2", text="Sara")

FILLED = """- textbox "Full name" [ref=e2]: Sara Khan
- textbox "Email" [ref=e3]: sara.example.com
- button "Create account" [ref=e9]"""
WIPED_WITH_ERROR = """- textbox "Full name" [ref=e2]
- textbox "Email" [invalid] [ref=e3]
- alert [ref=e4]: Email must contain @.
- button "Create account" [ref=e9]"""
KEPT_WITH_ERROR = """- textbox "Full name" [ref=e2]: Sara Khan
- textbox "Email" [invalid] [ref=e3]: sara.example.com
- alert [ref=e4]: Email must contain @.
- button "Create account" [ref=e9]"""
WIPED_NO_ERROR = """- textbox "Full name" [ref=e2]
- textbox "Email" [ref=e3]
- button "Create account" [ref=e9]"""


def obs(tree, step=0, url="/signup.html"):
    return Observation(step=step, tree=tree, url_path=url)


def record(step, executed=SUBMIT, goal=False):
    return StepRecord(
        run_id="r1",
        persona="error_prone",
        page="signup.html",
        step=step,
        observation_hash="h",
        intended_action=executed or TYPE,
        executed_action=executed,
        result="ok",
        goal_reached=goal,
    )


def run_log(observations, steps, submissions=(), status="gave_up"):
    meta = {"run_id": "r1", "persona": "error_prone", "page": "signup.html", "status": status}
    return RunLog(meta, steps, observations, list(submissions))


class TestDataLoss:
    def test_fields_wiped_on_error(self):
        run = run_log([obs(FILLED), obs(WIPED_WITH_ERROR, 1)], [record(0)])
        finding = data_loss_on_error(run)
        assert finding.signal == "data_loss_on_error" and finding.evidence_steps == [0]
        assert finding.candidate_criteria == ["Nielsen 9", "WCAG 3.3.7"]
        assert finding.severity == 4  # the task was not completed
        assert finding.confidence == 0.9

    def test_values_kept_on_error(self):
        run = run_log([obs(FILLED), obs(KEPT_WITH_ERROR, 1)], [record(0)])
        assert data_loss_on_error(run) is None

    def test_cleared_without_error_is_not_data_loss(self):
        # e.g. the user pressed a "Clear" button on purpose
        run = run_log([obs(FILLED), obs(WIPED_NO_ERROR, 1)], [record(0)])
        assert data_loss_on_error(run) is None

    def test_new_page_is_not_data_loss(self):
        run = run_log([obs(FILLED), obs(WIPED_WITH_ERROR, 1, url="/next.html")], [record(0)])
        assert data_loss_on_error(run) is None

    def test_only_the_invalid_field_cleared_is_fine(self):
        only_email = KEPT_WITH_ERROR.replace(": sara.example.com", "")
        assert lost_fields(obs(FILLED), obs(only_email)) == []

    def test_typing_is_not_a_submit(self):
        run = run_log([obs(FILLED), obs(WIPED_WITH_ERROR, 1)], [record(0, executed=TYPE)])
        assert data_loss_on_error(run) is None

    def test_skipped_action_is_not_a_submit(self):
        run = run_log([obs(FILLED), obs(WIPED_WITH_ERROR, 1)], [record(0, executed=None)])
        assert data_loss_on_error(run) is None

    def test_goal_reached_is_not_an_error(self):
        run = run_log([obs(FILLED), obs(WIPED_WITH_ERROR, 1)], [record(0, goal=True)])
        assert data_loss_on_error(run) is None

    def test_no_observation_after_the_last_step(self):
        assert data_loss_on_error(run_log([obs(FILLED)], [record(0)])) is None


def sub(step, body="kettle"):
    return Submission(step=step, method="POST", url="https://x/api/orders", body=body)


class TestDuplicateSubmission:
    def test_two_identical_requests_in_one_step(self):
        run = run_log([], [], [sub(1), sub(1)], status="succeeded")
        finding = duplicate_submission(run)
        assert finding.evidence_steps == [1]
        assert finding.candidate_criteria == ["Nielsen 5", "WCAG 3.3.4"]
        # Spec rule: completed without data loss is 2. Whether a duplicate order
        # should be 3 is a team decision; change it in grounding.severity.
        assert finding.severity == 2

    @pytest.mark.parametrize(
        "subs",
        [
            [sub(1)],  # one order
            [sub(1), sub(2)],  # submitted again later, on purpose
            [sub(1, "kettle"), sub(1, "toaster")],  # two different requests
        ],
    )
    def test_not_a_duplicate(self, subs):
        assert duplicate_submission(run_log([], [], subs)) is None


def test_detect_runs_every_detector():
    run = run_log([obs(FILLED), obs(WIPED_WITH_ERROR, 1)], [record(0)], [sub(0), sub(0)])
    assert sorted(f.signal for f in detect(run)) == ["data_loss_on_error", "duplicate_submission"]


class TestGroundingIsTheSource:
    """Candidates, severity and confidence come from grounding/, not the detectors."""

    def test_every_detector_signal_is_in_the_signal_map(self):
        run = run_log([obs(FILLED), obs(WIPED_WITH_ERROR, 1)], [record(0)], [sub(0), sub(0)])
        for finding in detect(run):
            assert finding.candidate_criteria == signal_map().candidates(finding.signal)

    def test_severity_follows_the_spec_rule(self):
        # grounding.severity: 3 only for data loss (or a long path) when completed.
        lost = run_log([obs(FILLED), obs(WIPED_WITH_ERROR, 1)], [record(0)], status="succeeded")
        double = run_log([], [], [sub(1), sub(1)], status="succeeded")
        assert data_loss_on_error(lost).severity == 3
        assert duplicate_submission(double).severity == 2
