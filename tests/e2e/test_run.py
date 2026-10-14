"""The command-line run (agent/run.py) on the real test app, with no API key."""

import subprocess
import sys

import pytest

from agent.fake_model import FakeModel, click
from agent.run import execute, report


def test_execute_runs_the_page_and_its_detectors(browser, tmp_path):
    # Seed 1 doubles P1's first click at the configured rates (the demo's seed).
    model = FakeModel([click("Place order")])
    result, findings = execute("order-a", 1, model, tmp_path, browser=browser)
    assert result.status == "succeeded"
    assert [f.signal for f in findings] == ["duplicate_submission"]
    text = report(result, findings)
    assert "double_submit" in text and "finding: duplicate_submission, severity 2" in text


def test_clean_page_has_no_finding(browser, tmp_path):
    model = FakeModel([click("Place order")])
    result, findings = execute("order-b", 1, model, tmp_path, browser=browser)
    assert result.steps[0].perturbation == "double_submit" and findings == []
    assert "findings: none" in report(result, findings)


def test_unknown_page_names_the_pages(browser, tmp_path):
    with pytest.raises(SystemExit, match="signup-a"):
        execute("nope", 1, FakeModel([]), tmp_path, browser=browser)


def test_command_line_replay_without_a_recording_aborts(tmp_path):
    # The real command in its own process: no recording, so no reply, so the
    # run is aborted (exit 1), never sent to the API.
    args = ["--page", "order-a", "--seed", "1", "--logs", str(tmp_path), "--replay"]
    done = subprocess.run(
        [sys.executable, "-m", "agent.run", *args], capture_output=True, text=True, timeout=120
    )
    assert done.returncode == 1, done.stderr
    assert "status: aborted_provider" in done.stdout and "no recorded reply" in done.stdout
    assert "REPLAY of recorded model replies" in done.stdout
