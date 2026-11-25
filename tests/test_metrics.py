"""Evaluation metrics on a synthetic runs.csv: no browser, no model."""

import csv

from agent import metrics
from agent.metrics import FIELDS, markdown, per_bug, read_runs, summarise


def row(bug, condition, seed, signals="", status="succeeded", perturbations="", **kw):
    expected = {"B1": "data_loss_on_error", "B4": "duplicate_submission"}[bug]
    base = {f: "" for f in FIELDS}
    base |= {
        "run_id": f"{bug}-{condition}-{seed}",
        "persona": "error_prone",
        "bug": bug,
        "page": f"{bug}.html",
        "condition": condition,
        "seed": str(seed),
        "status": status,
        "steps": "4",
        "seconds": "10",
        "signals": signals,
        "expected_signal": expected,
        "detected": str(int(expected in signals)),
        "perturbations": perturbations,
        "quotes_generated": str(2 * len([s for s in signals.split(";") if s])),
        "quotes_verified": str(2 * len([s for s in signals.split(";") if s])),
    }
    return base | kw


def b4_rows():
    rows = []
    for seed in range(1, 6):
        fired = seed != 5  # 4/5 in persona on buggy
        rows.append(
            row(
                "B4",
                "persona_buggy",
                seed,
                "duplicate_submission" if fired else "",
                perturbations="double_submit" if fired else "",
            )
        )
        rows.append(row("B4", "baseline_buggy", seed))
        rows.append(row("B4", "persona_clean", seed))
    return rows


def b1_rows():
    # Fires 2/5 on buggy, once on clean (a false positive), once excluded.
    rows = []
    for seed in range(1, 6):
        rows.append(
            row(
                "B1",
                "persona_buggy",
                seed,
                "data_loss_on_error" if seed <= 2 else "",
                perturbations="typo" if seed <= 3 else "",
            )
        )
        rows.append(row("B1", "baseline_buggy", seed))
        clean_signals = "duplicate_submission" if seed == 1 else ""
        rows.append(row("B1", "persona_clean", seed, clean_signals))
    rows.append(row("B1", "persona_buggy", 6, status="aborted_provider"))
    return rows


class TestPerBug:
    def test_stable_and_attributed(self):
        (b4,) = per_bug(b4_rows())
        assert b4.rates == {
            "persona_buggy": (4, 5),
            "baseline_buggy": (0, 5),
            "persona_clean": (0, 5),
        }
        assert b4.stable and b4.attributed
        assert b4.triggered == (4, 5) and b4.detected_given_trigger == (4, 4)

    def test_unstable_is_not_attributed(self):
        (b1,) = per_bug(b1_rows())
        assert b1.rates["persona_buggy"] == (2, 5)  # the aborted run is excluded
        assert not b1.stable and not b1.attributed
        assert b1.triggered == (3, 5) and b1.detected_given_trigger == (2, 3)

    def test_baseline_firing_removes_attribution(self):
        rows = [
            r | {"signals": "duplicate_submission"} if r["condition"] == "baseline_buggy" else r
            for r in b4_rows()
        ]
        (b4,) = per_bug(rows)
        assert b4.stable and not b4.attributed

    def test_no_baseline_is_found_not_attributed(self):
        # Smoke runs skip the baseline: nothing shows any user would miss it.
        rows = [r for r in b4_rows() if r["condition"] != "baseline_buggy"]
        (b4,) = per_bug(rows)
        assert b4.found and not b4.attributed

    def test_bugs_in_natural_order(self):
        rows = [row("B4", "persona_buggy", 1), row("B1", "persona_buggy", 1)]
        assert [b.bug for b in per_bug(rows)] == ["B1", "B4"]


class TestSummary:
    def test_totals(self):
        s = summarise(b1_rows() + b4_rows())
        assert s.runs == 31 and s.excluded == 1
        assert s.recall == 0.5  # B4 attributed, B1 not
        # persona findings: B1 buggy 2 + B1 clean 1 + B4 buggy 4 = 7; correct = 6
        assert s.precision == round(6 / 7, 3)
        assert s.false_positive_rate == round(1 / 10, 3)
        assert s.citation_validity == 1.0
        assert s.mean_steps == 4.0

    def test_empty(self):
        s = summarise([])
        assert s.recall is None and s.precision is None and s.runs == 0

    def test_markdown_shows_k_of_n(self):
        text = markdown(b4_rows())
        assert "| B4 | `duplicate_submission` | 4/5 | 0/5 | 0/5 | 4/5 | 4/4 | yes | yes |" in text


def test_csv_round_trip(tmp_path):
    path = tmp_path / "runs.csv"
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(b4_rows())
    assert per_bug(read_runs(path)) == per_bug(b4_rows())


def test_stable_threshold():
    assert metrics.stable(4, 5) and not metrics.stable(3, 5) and not metrics.stable(0, 0)
