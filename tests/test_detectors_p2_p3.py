"""B3, P2 and P3 detectors on hand-built run logs (no browser)."""

from agent.contracts import Action, Observation, StepRecord
from agent.detectors import RunLog, detect
from agent.detectors.error_not_actionable import error_not_actionable, vague_error
from agent.detectors.low_literacy import (
    instruction_unintelligible,
    label_unintelligible,
    system_language,
)
from agent.detectors.memoryless import lost_location, no_progress_indicator, recall_required

CLICK = Action(thought="", action="click", ref="e9")


def obs(tree, step=0, url="/p.html"):
    return Observation(step=step, tree=tree, url_path=url)


def rec(step, action=CLICK, persona="error_prone"):
    return StepRecord(
        run_id="r",
        persona=persona,
        page="p.html",
        step=step,
        observation_hash="h",
        intended_action=action,
        executed_action=action,
        result="ok",
        goal_reached=False,
    )


def log(observations, steps=(), persona="error_prone", status="gave_up", titles=()):
    meta = {"run_id": "r", "persona": persona, "page": "p.html", "status": status}
    return RunLog(meta, list(steps), observations, [], list(titles))


FORM = """- textbox "Phone number" [ref=e2]: "0300"
- button "Request callback" [ref=e9]"""


class TestErrorNotActionable:
    def vague(self, text):
        return f"""- textbox "Phone number" [invalid] [ref=e2]: "0300"
- alert [ref=e3]: {text}
- button "Request callback" [ref=e9]"""

    def test_vague_error(self):
        run = log([obs(FORM), obs(self.vague("Invalid input."), 1)], [rec(0)])
        assert error_not_actionable(run).evidence_steps == [0]

    def test_error_naming_the_field(self):
        assert vague_error(obs(self.vague("Phone number must be 11 digits."))) is None
        assert vague_error(obs(self.vague("Enter your phone."))) is None

    def test_error_with_an_example(self):
        assert vague_error(obs(self.vague("Invalid, try like this one."))) is None


def screen(heading, button, extra=""):
    return f"""- heading "Change your plan" [level=1] [ref=e1]
- heading "{heading}" [level=2] [ref=e2]
{extra}- button "{button}" [ref=e9]"""


class TestP2:
    def test_recall_required(self):
        step1 = "\n".join(
            [
                "- paragraph [ref=e1]: Your return reference is RTN-48213.",
                '- button "Continue" [ref=e9]',
            ]
        )
        step3 = '- textbox "Return reference" [ref=e2]\n- button "Book return" [ref=e9]'
        run = log([obs(step1), obs(step3, 1)], [rec(0, persona="memoryless")], "memoryless")
        assert recall_required(run).evidence_steps == [1]
        reminded = step3 + "\n- paragraph [ref=e3]: Your return reference is RTN-48213."
        run = log([obs(step1), obs(reminded, 1)], [rec(0)], "memoryless")
        assert recall_required(run) is None

    def test_no_progress_indicator(self):
        a = screen("Choose", "Continue", '- radio "Family" [ref=e3]\n')
        b = screen("Choose", "Confirm change")
        assert no_progress_indicator(log([obs(a), obs(b, 1)])).evidence_steps == [0, 1]
        numbered = screen("Step 1 of 3: Choose", "Continue")
        assert no_progress_indicator(log([obs(numbered), obs(b, 1)])) is None

    def test_lost_location(self):
        a, b = screen("A", "Continue"), screen("B", "Renew")
        observations = [obs(a), obs(a, 1), obs(a, 2), obs(b, 3)]
        same = ["Plus – SimShop"] * 4
        assert lost_location(log(observations, titles=same)).evidence_steps == [0, 1, 2]
        named = ["Step 1"] * 3 + ["Step 2"]
        assert lost_location(log(observations, titles=named)) is None
        assert lost_location(log(observations)) is None  # titles not logged


class TestP3:
    def test_label_unintelligible(self):
        tree = '- button "[unknown] [unknown]" [ref=e9]'
        assert label_unintelligible(log([obs(tree)], persona="low_literacy"))
        assert label_unintelligible(log([obs(tree)], status="succeeded")) is None
        assert label_unintelligible(log([obs('- button "Send money" [ref=e9]')])) is None

    def test_instruction_unintelligible(self):
        jargon = (
            "- paragraph [ref=e1]: '[unknown] any provision [unknown], [unknown] shall be "
            "[unknown] [unknown] upon the [unknown] of the [unknown] STOP'"
        )
        assert instruction_unintelligible(log([obs(jargon)]))
        plain = "- paragraph [ref=e1]: To end your membership, type the word STOP in the box below."
        assert instruction_unintelligible(log([obs(plain)])) is None

    def test_system_language(self):
        assert system_language(log([obs("- alert [ref=e1]: '[unknown]_[unknown]_422'")]))
        assert system_language(log([obs("- alert [ref=e1]: ERR422")]))
        assert (
            system_language(log([obs("- alert [ref=e1]: Enter 11 digits, like 03001234567.")]))
            is None
        )


def test_each_persona_runs_only_its_own_detectors():
    # A P1-shaped vague error and a P3-shaped code; each persona reports its own.
    tree = """- textbox "Phone number" [invalid] [ref=e2]: "0300"
- alert [ref=e3]: ERR_VALIDATION_422
- button "Save" [ref=e9]"""
    observations = [obs(FORM), obs(tree, 1)]
    p1 = detect(log(observations, [rec(0)], "error_prone"))
    p3 = detect(log(observations, [rec(0, persona="low_literacy")], "low_literacy"))
    assert [f.signal for f in p1] == ["error_not_actionable"]
    assert [f.signal for f in p3] == ["system_language"]


def test_shared_detectors_follow_the_signal_map():
    """`also:` in the signal map: P10 reuses P1's duplicate_submission and P6
    reuses P7's reflow_failure."""
    from agent.detectors import detectors_for

    def names(persona):
        return {d.__name__ for d in detectors_for(persona)}

    assert "duplicate_submission" in names("slow_network")
    assert "reflow_failure" in names("touch_imprecise")
    assert "duplicate_submission" not in names("memoryless")
