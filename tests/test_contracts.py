import pytest
from pydantic import ValidationError

from agent.contracts import Action, Citation, Finding, Observation, StepRecord


def act(**kw):
    return Action(thought="t", **kw)


class TestAction:
    def test_click_with_ref(self):
        assert act(action="click", ref="e3").ref == "e3"

    def test_unknown_action_rejected(self):
        with pytest.raises(ValidationError):
            act(action="hover", ref="e1")

    @pytest.mark.parametrize("ref", ["#submit", "button", "e", "E1", "e1 "])
    def test_ref_must_be_harness_ref(self, ref):
        with pytest.raises(ValidationError):
            act(action="click", ref=ref)

    @pytest.mark.parametrize(
        "kw",
        [
            {"action": "click"},
            {"action": "type", "ref": "e1"},
            {"action": "type", "text": "x"},
            {"action": "press"},
            {"action": "back", "ref": "e1"},
            {"action": "give_up", "text": "done"},
        ],
    )
    def test_missing_or_extra_fields_rejected(self, kw):
        with pytest.raises(ValidationError):
            act(**kw)

    def test_extra_keys_rejected(self):
        with pytest.raises(ValidationError):
            act(action="back", selector="#x")

    def test_model_cannot_declare_success(self):
        # Success is harness-decided: there is no "done"/"success" action.
        with pytest.raises(ValidationError):
            act(action="success")


class TestObservation:
    def test_minimal(self):
        obs = Observation(step=0, tree='- button "Send" [ref=e1]', url_path="/p1.html")
        assert obs.focused is None and obs.persona_notes == []

    def test_negative_step_rejected(self):
        with pytest.raises(ValidationError):
            Observation(step=-1, tree="", url_path="/")


class TestStepRecord:
    def base(self, **kw):
        fields = dict(
            run_id="r1",
            persona="error_prone",
            page="b1.html",
            step=2,
            observation_hash="abc",
            intended_action=act(action="type", ref="e2", text="ali@example.com"),
            executed_action=act(action="type", ref="e2", text="ali@exmaple.com"),
            perturbation="typo",
            result="ok",
            goal_reached=False,
        )
        fields.update(kw)
        return StepRecord(**fields)

    def test_intended_and_executed_kept_separately(self):
        rec = self.base()
        assert rec.intended_action.text != rec.executed_action.text

    def test_dropped_action_allowed(self):
        assert self.base(executed_action=None, perturbation="skip_field").executed_action is None

    def test_unknown_result_rejected(self):
        with pytest.raises(ValidationError):
            self.base(result="passed")


class TestFinding:
    def base(self, **kw):
        fields = dict(
            finding_id="f1",
            persona="error_prone",
            page="b1.html",
            signal="data_loss_on_error",
            evidence_steps=[3, 4],
            candidate_criteria=["WCAG 3.3.7", "Nielsen #9"],
            citations=[Citation(source="WCAG", criterion_id="WCAG 3.3.7", quote="Information")],
            severity=3,
            confidence=0.9,
            baseline_reproduced=False,
        )
        fields.update(kw)
        return Finding(**fields)

    def test_valid(self):
        assert self.base().severity == 3

    @pytest.mark.parametrize("severity", [0, 5])
    def test_severity_range(self, severity):
        with pytest.raises(ValidationError):
            self.base(severity=severity)

    @pytest.mark.parametrize("confidence", [-0.1, 1.1])
    def test_confidence_range(self, confidence):
        with pytest.raises(ValidationError):
            self.base(confidence=confidence)

    def test_needs_evidence(self):
        with pytest.raises(ValidationError):
            self.base(evidence_steps=[])

    def test_citation_outside_candidates_rejected(self):
        # The LLM never chooses the criterion: citations must come from the signal map.
        bad = Citation(source="WCAG", criterion_id="WCAG 1.4.3", quote="contrast")
        with pytest.raises(ValidationError):
            self.base(citations=[bad])

    def test_empty_quote_rejected(self):
        with pytest.raises(ValidationError):
            Citation(source="Nielsen", criterion_id="Nielsen #9", quote="")
