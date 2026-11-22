"""agent.evaluate end to end with the fake model: rows, files and resume."""

from agent import metrics
from agent.evaluate import bugs_for, evaluate
from agent.fake_model import FakeModel, click


def test_bugs_in_scope_follow_the_signal_map():
    assert [b.id for b in bugs_for("error_prone")] == ["B1", "B2", "B3", "B4", "B5", "B6"]
    assert [b.id for b in bugs_for("memoryless")] == ["B7", "B8", "B9"]


def test_evaluate_writes_rows_summary_and_resumes(browser, tmp_path):
    lines = []

    def model():
        return FakeModel([click("Place order")])

    rows = evaluate(
        "error_prone", 2, tmp_path, model, only=["B4"], browser=browser, log=lines.append
    )
    assert len(rows) == 6  # 3 conditions x 2 seeds
    assert {r["condition"] for r in rows} == {"persona_buggy", "baseline_buggy", "persona_clean"}
    assert all(r["status"] == "succeeded" for r in rows)
    assert len(metrics.read_runs(tmp_path / "runs.csv")) == 6
    assert "| B4 | `duplicate_submission` |" in (tmp_path / "summary.md").read_text("utf-8")
    assert (tmp_path / "metrics.json").exists()
    for r in rows:
        assert (tmp_path / r["log_dir"] / "steps.jsonl").exists()

    lines.clear()
    again = evaluate(
        "error_prone", 2, tmp_path, model, only=["B4"], browser=browser, log=lines.append
    )
    assert len(again) == 6 and "0 to run" in lines[0]


def test_rescore_rereads_the_logs(browser, tmp_path):
    from agent.evaluate import _write_all, rescore

    def model():
        return FakeModel([click("Delete account"), click("Yes, delete my account")])

    rows = evaluate("error_prone", 1, tmp_path, model, only=["B5"], browser=browser, log=print)
    assert "destructive_without_confirm" in rows[0]["signals"]  # persona on buggy
    # As if the runs were made before any detector existed.
    _write_all(tmp_path / "runs.csv", [r | {"signals": "", "detected": 0} for r in rows])
    rescored = rescore("error_prone", tmp_path)
    assert [r["signals"] for r in rescored] == [r["signals"] for r in rows]
    assert "| B5 | `destructive_without_confirm` | 1/1 |" in (tmp_path / "summary.md").read_text(
        "utf-8"
    )
