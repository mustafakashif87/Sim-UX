"""`simux run` gates like the GitHub Action: exit 1 on order-a, 0 on order-b."""

import json
from pathlib import Path

import pytest

from agent.cli import main

FIXTURES = Path(__file__).parents[2] / "examples" / "action-fixture"


@pytest.mark.parametrize("page, code", [("order-a", 1), ("order-b", 0)])
def test_exit_code_follows_the_findings(browser, tmp_path, page, code):
    out = tmp_path / "findings.json"
    summary = tmp_path / "summary.md"
    args = ["run", "--config", str(FIXTURES / f"{page}.simux.yaml"), "--out", str(out)]
    args += ["--logs", str(tmp_path / "logs"), "--summary", str(summary)]
    assert main(args, browser=browser) == code
    report = json.loads(out.read_text("utf-8"))
    assert report["failed"] == (code == 1)
    signals = [f["signal"] for f in report["findings"]]
    assert signals == (["duplicate_submission"] if code else [])
    assert "## SimUX findings" in summary.read_text("utf-8")
