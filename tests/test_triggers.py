"""When a run's mistake reached its bug (agent/triggers.py), and the metrics
that use it: found vs attributed recall, and the triggered condition."""

from agent.contracts import Action, Observation, StepRecord
from agent.detectors import RunLog, Submission
from agent.metrics import FIELDS, markdown, per_bug, summarise
from agent.triggers import triggered

FORM = """- textbox "Email address" [ref=e2]: sam.example.com
- button "Subscribe" [ref=e3]"""
TYPE = Action(thought="", action="type", ref="e2", text="sam@example.com")
CLICK = Action(thought="", action="click", ref="e3")


def rec(step, action, perturbation=None, goal=False):
    return StepRecord(
        run_id="r",
        persona="error_prone",
        page="p.html",
        step=step,
        observation_hash="h",
        intended_action=action,
        executed_action=action,
        perturbation=perturbation,
        result="ok",
        goal_reached=goal,
    )


def log(steps, submissions=()):
    obs = [Observation(step=i, tree=FORM, url_path="/p.html") for i in range(len(steps) + 1)]
    meta = {"run_id": "r", "persona": "error_prone", "page": "p.html", "status": "gave_up"}
    return RunLog(meta, steps, obs, list(submissions))


def sent(step):
    return Submission(step=step, method="POST", url="https://x/api", body="b")


class TestTriggered:
    def test_typo_then_rejected_submit(self):
        run = log([rec(0, TYPE, "typo"), rec(1, CLICK)])
        assert triggered("error_not_identified", run)

    def test_typo_but_submit_accepted(self):
        # The typo did not matter: the page took the submission.
        run = log([rec(0, TYPE, "typo"), rec(1, CLICK, goal=True)], [sent(1)])
        assert not triggered("data_loss_on_error", run)

    def test_no_slip_no_trigger(self):
        assert not triggered("error_not_actionable", log([rec(0, TYPE), rec(1, CLICK)]))

    def test_double_press_that_sent(self):
        run = log([rec(0, CLICK, "double_submit")], [sent(0), sent(0)])
        assert triggered("duplicate_submission", run)
        assert not triggered("duplicate_submission", log([rec(0, CLICK)], [sent(0)]))

    def test_signals_without_a_mistake_always_count(self):
        assert triggered("destructive_without_confirm", log([rec(0, CLICK)]))


def row(bug, condition, seed, signals="", triggered_=""):
    expected = {"B2": "error_not_identified", "B5": "destructive_without_confirm"}[bug]
    base = {f: "" for f in FIELDS}
    return base | {
        "bug": bug,
        "condition": condition,
        "seed": str(seed),
        "status": "gave_up",
        "steps": "3",
        "seconds": "5",
        "signals": signals,
        "expected_signal": expected,
        "triggered": triggered_,
        "quotes_generated": "0",
        "quotes_verified": "0",
    }


def test_found_vs_attributed():
    rows = []
    for seed in range(1, 6):
        rows += [
            row("B5", "persona_buggy", seed, "destructive_without_confirm", "1"),
            row("B5", "baseline_buggy", seed, "destructive_without_confirm", "1"),
            row("B5", "persona_clean", seed, "", "1"),
        ]
    (b5,) = per_bug(rows)
    assert b5.found and not b5.attributed  # any user hits it
    s = summarise(rows)
    assert s.found_recall == 1.0 and s.recall == 0.0


def test_logged_trigger_column_and_triggered_condition():
    rows = [
        row("B2", "persona_buggy", 1, "error_not_identified", "1"),
        row("B2", "persona_buggy", 2, "", "0"),
        row("B2", "triggered_buggy", 1, "error_not_identified", "1"),
        row("B2", "triggered_buggy", 2, "error_not_identified", "1"),
        row("B2", "triggered_buggy", 3, "", "0"),  # mistake never reached the bug
    ]
    (b2,) = per_bug(rows)
    assert b2.triggered == (1, 2) and b2.detected_given_trigger == (1, 1)
    assert b2.forced == (2, 2)
    assert "| B2 | 2/2 |" in markdown(rows)
    # The triggered condition is never counted as a persona run for precision.
    assert summarise(rows).precision == 1.0
