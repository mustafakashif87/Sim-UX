"""Grounding stub: map, corpus, quote verification, severity. No LLM, no browser."""

import pytest

from agent.contracts import Finding
from agent.detectors import CANDIDATES
from grounding import (
    default_corpus,
    default_signal_map,
    ground_finding,
    key_quotes,
    severity,
    start_confidence,
    verify_quote,
)

CORPUS = default_corpus()
SIGNALS = default_signal_map()

# Spec, persona tables: the signals each persona is expected to produce.
P1 = [
    "data_loss_on_error",
    "error_not_identified",
    "error_not_actionable",
    "duplicate_submission",
    "destructive_without_confirm",
    "no_way_back",
]
P2 = ["recall_required", "lost_location", "no_progress_indicator"]
P3 = ["label_unintelligible", "instruction_unintelligible", "system_language"]
# test-app/SEEDED_BUGS.md, "Expected signal" for SB-01 to SB-05.
FIXTURE_SIGNALS = ["image-alt", "button-name", "label", "keyboard_trap", "unreachable_control"]


def finding(signal="data_loss_on_error", confidence=0.9) -> Finding:
    return Finding(
        finding_id="r1-" + signal,
        persona="error_prone",
        page="signup-a.html",
        signal=signal,
        evidence_steps=[2],
        candidate_criteria=SIGNALS.candidates(signal),
        severity=3,
        confidence=confidence,
        baseline_reproduced=False,
    )


class TestSignalMap:
    @pytest.mark.parametrize("signal", P1 + P2 + P3 + FIXTURE_SIGNALS)
    def test_every_spec_signal_is_mapped(self, signal):
        assert signal in SIGNALS and SIGNALS.candidates(signal)

    def test_every_candidate_is_in_the_corpus(self):
        assert SIGNALS.check_against(CORPUS) == []

    def test_types_are_known(self):
        assert {SIGNALS.entry(s).type for s in SIGNALS.signals()} <= {
            "deterministic",
            "model_judged",
        }

    def test_model_judged_signals_match_the_spec(self):
        judged = {s for s in SIGNALS.signals() if SIGNALS.entry(s).type == "model_judged"}
        assert judged == {"error_not_actionable", "system_language"}

    def test_detectors_interim_map_agrees(self):
        for signal, criteria in CANDIDATES.items():
            assert SIGNALS.candidates(signal) == criteria

    def test_nielsen_only_signals_have_no_wcag(self):
        # Spec: no_way_back and system_language have no WCAG criterion.
        for signal in ("no_way_back", "system_language"):
            assert all(c.startswith("Nielsen") for c in SIGNALS.candidates(signal))


class TestCorpus:
    def test_key_quote_is_verbatim_in_text(self):
        for criterion_id in CORPUS.ids():
            entry = CORPUS.get(criterion_id)
            assert verify_quote(entry.key_quote, entry), criterion_id

    def test_entries_carry_a_source_and_a_url(self):
        for criterion_id in CORPUS.ids():
            entry = CORPUS.get(criterion_id)
            assert entry.source in ("WCAG", "Nielsen") and entry.url.startswith("https://")
            assert criterion_id.startswith(entry.source)

    def test_nielsen_excerpts_stay_short(self):
        # NN/g owns the article: keep short attributed excerpts, not the text.
        for criterion_id in CORPUS.ids():
            if criterion_id.startswith("Nielsen"):
                assert len(CORPUS.get(criterion_id).text.split()) <= 60

    def test_wcag_text_has_no_html_leftovers(self):
        for criterion_id in CORPUS.ids():
            assert "<" not in CORPUS.get(criterion_id).text


class TestVerifyQuote:
    entry = CORPUS.get("WCAG 3.3.1")

    def test_exact_substring_passes(self):
        assert verify_quote("the item that is in error is identified", self.entry)

    def test_whitespace_runs_are_collapsed(self):
        assert verify_quote("the item that  is in\nerror is identified", self.entry)

    def test_paraphrase_is_rejected(self):
        assert not verify_quote(
            "the field in error must be named and described in text", self.entry
        )

    def test_case_change_is_rejected(self):
        assert not verify_quote("The Item That Is In Error Is Identified", self.entry)

    def test_empty_quote_is_rejected(self):
        assert not verify_quote("   ", self.entry)


class TestGroundFinding:
    def test_verified_quote_becomes_a_citation(self):
        f = finding()
        report = ground_finding(f, CORPUS, key_quotes(SIGNALS, CORPUS, f.signal))
        assert report.grounded and report.dropped == []
        assert {c.criterion_id for c in report.finding.citations} == {"Nielsen 9", "WCAG 3.3.7"}
        assert {c.source for c in report.finding.citations} == {"Nielsen", "WCAG"}
        assert report.finding.confidence == 0.9

    @pytest.mark.parametrize("signal", P1 + P2 + P3 + FIXTURE_SIGNALS)
    def test_key_quotes_ground_every_mapped_signal(self, signal):
        f = finding(signal)
        report = ground_finding(f, CORPUS, key_quotes(SIGNALS, CORPUS, signal))
        assert report.grounded and report.dropped == []

    def test_paraphrased_quote_is_dropped_and_finding_is_ungrounded(self):
        f = finding()
        report = ground_finding(f, CORPUS, {"WCAG 3.3.7": "users should not retype their data"})
        assert not report.grounded and report.finding.citations == []
        assert report.dropped == [("WCAG 3.3.7", "quote is not in the corpus text")]
        assert report.finding.confidence == pytest.approx(0.45)

    def test_ungrounded_finding_is_still_returned(self):
        f = finding()
        report = ground_finding(f, CORPUS, {})
        assert report.finding.signal == f.signal and report.finding.evidence_steps == [2]

    def test_criterion_outside_the_candidates_is_dropped(self):
        f = finding()
        quote = CORPUS.get("WCAG 3.3.1").key_quote
        report = ground_finding(f, CORPUS, {"WCAG 3.3.1": quote})
        assert not report.grounded
        assert report.dropped == [("WCAG 3.3.1", "not a candidate for this signal")]

    def test_one_good_quote_keeps_the_finding_grounded(self):
        f = finding()
        quotes = {
            "Nielsen 9": CORPUS.get("Nielsen 9").key_quote,
            "WCAG 3.3.7": "made up wording",
        }
        report = ground_finding(f, CORPUS, quotes)
        assert report.grounded and len(report.finding.citations) == 1
        assert report.finding.confidence == 0.9
        assert [d[0] for d in report.dropped] == ["WCAG 3.3.7"]

    def test_quote_from_another_entry_is_rejected(self):
        f = finding()
        report = ground_finding(f, CORPUS, {"WCAG 3.3.7": CORPUS.get("Nielsen 9").key_quote})
        assert not report.grounded


class TestSeverityAndConfidence:
    def test_blocked_task_is_4(self):
        assert severity(task_completed=False) == 4

    def test_data_loss_is_3(self):
        assert severity(task_completed=True, data_loss=True) == 3

    def test_more_than_twice_the_shortest_path_is_3(self):
        assert severity(task_completed=True, steps=9, shortest_steps=4) == 3
        assert severity(task_completed=True, steps=8, shortest_steps=4) == 2

    def test_recoverable_friction_is_2_and_cosmetic_is_1(self):
        assert severity(task_completed=True) == 2
        assert severity(task_completed=True, cosmetic=True) == 1

    def test_confidence_starts_by_type_and_scales_by_reproduction(self):
        assert start_confidence("deterministic") == 0.9
        assert start_confidence("model_judged") == 0.6
        assert start_confidence("deterministic", 4 / 5) == pytest.approx(0.72)
