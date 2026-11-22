"""Detectors on hand-built run logs: no browser, so edge cases are cheap."""

import json

import pytest

from agent.contracts import Action, Observation, StepRecord
from agent.detectors import RunLog, Submission, audit, detect, signal_map
from agent.detectors.data_loss import data_loss_on_error, lost_fields
from agent.detectors.destructive import destructive_without_confirm
from agent.detectors.duplicate_submission import duplicate_submission
from agent.detectors.error_not_identified import error_not_identified
from agent.detectors.no_way_back import no_way_back
from agent.detectors.redundant_entry import redundant_entry

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


def test_aborted_run_has_no_findings():
    # The model could not answer; the same evidence says nothing about the page.
    run = run_log(
        [obs(FILLED), obs(WIPED_WITH_ERROR, 1)], [record(0)], [sub(0), sub(0)], "aborted_provider"
    )
    assert detect(run) == []


def write_log(log_dir, run: RunLog) -> None:
    """Write a RunLog to disk in the layout agent/loop.py uses."""
    log_dir.mkdir()
    (log_dir / "run.json").write_text(json.dumps(run.meta), encoding="utf-8")
    (log_dir / "steps.jsonl").write_text(
        "".join(s.model_dump_json() + "\n" for s in run.steps), encoding="utf-8"
    )
    (log_dir / "observations.jsonl").write_text(
        "".join(
            json.dumps({"step": o.step, "observation": o.model_dump()}) + "\n"
            for o in run.observations
        ),
        encoding="utf-8",
    )
    (log_dir / "network.jsonl").write_text(
        "".join(json.dumps(vars(s)) + "\n" for s in run.submissions), encoding="utf-8"
    )


def test_audit_reads_the_log_and_grounds_each_finding(tmp_path):
    run = run_log([obs(FILLED), obs(WIPED_WITH_ERROR, 1)], [record(0)], [sub(0), sub(0)])
    write_log(tmp_path / "r1", run)
    findings = audit(tmp_path / "r1")
    assert sorted(f.signal for f in findings) == ["data_loss_on_error", "duplicate_submission"]
    for f in findings:
        assert f.citations, f"{f.signal} has no verified citation"
        assert {c.criterion_id for c in f.citations} <= set(f.candidate_criteria)


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


# --- error_not_identified (B2) ----------------------------------------------

SUBSCRIBE = """- textbox "Email address" [ref=e2]: sam.example.com
- button "Subscribe" [ref=e3]"""
SUBSCRIBE_ERROR = """- textbox "Email address" [invalid] [ref=e2]: sam.example.com
- alert [ref=e4]: Enter an email address like name@example.com.
- button "Subscribe" [ref=e3]"""
CLICK_SUBSCRIBE = Action(thought="", action="click", ref="e3")


class TestErrorNotIdentified:
    def test_silent_rejection(self):
        run = run_log([obs(SUBSCRIBE), obs(SUBSCRIBE, 1)], [record(0, CLICK_SUBSCRIBE)])
        finding = error_not_identified(run)
        assert finding.evidence_steps == [0]
        assert finding.candidate_criteria == ["Nielsen 9", "WCAG 3.3.1"]

    def test_error_shown_is_fine(self):
        run = run_log([obs(SUBSCRIBE), obs(SUBSCRIBE_ERROR, 1)], [record(0, CLICK_SUBSCRIBE)])
        assert error_not_identified(run) is None

    def test_same_error_again_is_fine(self):
        run = run_log([obs(SUBSCRIBE_ERROR), obs(SUBSCRIBE_ERROR, 1)], [record(0, CLICK_SUBSCRIBE)])
        assert error_not_identified(run) is None

    def test_request_sent_is_not_a_rejection(self):
        run = run_log([obs(SUBSCRIBE), obs(SUBSCRIBE, 1)], [record(0, CLICK_SUBSCRIBE)], [sub(0)])
        assert error_not_identified(run) is None

    def test_empty_form_is_not_judged(self):
        empty = SUBSCRIBE.replace(": sam.example.com", "")
        run = run_log([obs(empty), obs(empty, 1)], [record(0, CLICK_SUBSCRIBE)])
        assert error_not_identified(run) is None

    def test_enter_counts_as_submit(self):
        enter = Action(thought="", action="press", key="Enter")
        run = run_log([obs(SUBSCRIBE), obs(SUBSCRIBE, 1)], [record(0, enter)])
        assert error_not_identified(run).evidence_steps == [0]

    def test_clicking_a_link_is_not_a_submit(self):
        tree = SUBSCRIBE + '\n- link "Help" [ref=e5]'
        link = Action(thought="", action="click", ref="e5")
        assert error_not_identified(run_log([obs(tree), obs(tree, 1)], [record(0, link)])) is None


# --- destructive_without_confirm (B5) ---------------------------------------

SETTINGS = """- heading "Account settings" [level=1] [ref=e1]
- button "Delete account" [ref=e2]"""
DIALOG = """- heading "Account settings" [level=1] [ref=e1]
- button "Delete account" [ref=e2]
- dialog "Delete your account?" [ref=e3]:
  - button "Yes, delete my account" [ref=e4]
  - button "Cancel" [ref=e5]"""
DELETE = Action(thought="", action="click", ref="e2")
YES = Action(thought="", action="click", ref="e4")


def delete_sub(step):
    return Submission(step=step, method="POST", url="https://x/api/account/delete", body="s")


class TestDestructiveWithoutConfirm:
    def test_deletes_at_once(self):
        run = run_log([obs(SETTINGS), obs("", 1)], [record(0, DELETE)], [delete_sub(0)])
        finding = destructive_without_confirm(run)
        assert finding.evidence_steps == [0]
        assert finding.candidate_criteria == ["Nielsen 5", "Nielsen 3", "WCAG 3.3.4"]

    def test_asks_first(self):
        run = run_log(
            [obs(SETTINGS), obs(DIALOG, 1), obs("", 2)],
            [record(0, DELETE), record(1, YES)],
            [delete_sub(1)],
        )
        assert destructive_without_confirm(run) is None

    def test_destructive_click_that_sends_nothing(self):
        run = run_log([obs(SETTINGS), obs(DIALOG, 1)], [record(0, DELETE)])
        assert destructive_without_confirm(run) is None

    def test_ordinary_submit_is_not_destructive(self):
        run = run_log([obs(FILLED), obs("", 1)], [record(0)], [sub(0)])
        assert destructive_without_confirm(run) is None


# --- no_way_back --------------------------------------------------------------

STEP1 = """- heading "Your details" [level=2] [ref=e1]
- textbox "Full name" [ref=e2]: Sam Khan
- button "Continue" [ref=e3]"""
STEP1_WIPED = STEP1.replace(": Sam Khan", "")
STEP2 = """- heading "Confirm" [level=2] [ref=e1]
- button "Confirm" [ref=e2]"""
BACK = Action(thought="", action="back")
CONTINUE = Action(thought="", action="click", ref="e3")


class TestNoWayBack:
    def test_state_restored(self):
        run = run_log(
            [obs(STEP2), obs(STEP1, 1), obs(STEP2, 2)],
            [record(0, BACK), record(1, CONTINUE)],
        )
        assert no_way_back(run) is None

    def test_values_lost_and_never_restored(self):
        error = STEP1_WIPED + "\n- alert [ref=e4]: Enter your name."
        run = run_log(
            [obs(STEP2), obs(STEP1_WIPED, 1), obs(error, 2)],
            [record(0, BACK), record(1, CONTINUE)],
        )
        finding = no_way_back(run)
        assert finding.evidence_steps == [0] and finding.candidate_criteria == ["Nielsen 3"]

    def test_failed_back_leaves_the_screen(self):
        run = run_log([obs(STEP2), obs(STEP2, 1)], [record(0, BACK)])
        assert no_way_back(run) is None

    def test_restored_too_late(self):
        o = [obs(STEP2), *[obs(STEP1_WIPED, i) for i in range(1, 5)], obs(STEP2, 5)]
        steps = [record(0, BACK), *[record(i, CONTINUE) for i in range(1, 5)]]
        assert no_way_back(run_log(o, steps)).evidence_steps == [0]

    def test_success_soon_after_is_not_judged(self):
        run = run_log(
            [obs(STEP2), obs(STEP1_WIPED, 1), obs("", 2)],
            [record(0, BACK), record(1, CONTINUE, goal=True)],
            status="succeeded",
        )
        assert no_way_back(run) is None


# --- redundant_entry (B6) -----------------------------------------------------

DELIVERY = """- textbox "Street address" [ref=e2]
- button "Continue" [ref=e3]"""
BILLING_EMPTY = """- textbox "Billing street address" [ref=e2]
- button "Place order" [ref=e3]"""
BILLING_FILLED = """- textbox "Billing street address" [ref=e2]: 12 Canal Road
- button "Place order" [ref=e3]"""


def typed(step, text):
    action = Action(thought="", action="type", ref="e2", text=text)
    return record(step, action)


class TestRedundantEntry:
    def test_same_value_asked_again(self):
        run = run_log(
            [obs(DELIVERY), obs(BILLING_EMPTY, 1), obs(BILLING_FILLED, 2)],
            [typed(0, "12 Canal Road"), typed(1, " 12 canal road ")],
        )
        finding = redundant_entry(run)
        assert finding.evidence_steps == [1]
        assert finding.candidate_criteria == ["WCAG 3.3.7", "Nielsen 6"]

    def test_prefilled_field_is_fine(self):
        run = run_log(
            [obs(DELIVERY), obs(BILLING_FILLED, 1), obs(BILLING_FILLED, 2)],
            [typed(0, "12 Canal Road"), typed(1, "12 Canal Road")],
        )
        assert redundant_entry(run) is None

    def test_retyping_the_same_field_is_fine(self):
        run = run_log(
            [obs(DELIVERY), obs(DELIVERY, 1), obs(DELIVERY, 2)],
            [typed(0, "12 Canal Road"), typed(1, "12 Canal Road")],
        )
        assert redundant_entry(run) is None

    def test_short_values_do_not_count(self):
        run = run_log(
            [obs(DELIVERY), obs(BILLING_EMPTY, 1), obs(BILLING_EMPTY, 2)],
            [typed(0, "1"), typed(1, "1")],
        )
        assert redundant_entry(run) is None
