"""The demo command (agent/demo.py), run as the presenter would, with no API key.

Each test runs the real command in its own process on a copy of the recorded
demo runs (logs/demo/llm-cache), so logs/demo itself is never written.
"""

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from agent import llm
from agent.contracts import Observation
from agent.demo import make_model

RECORDING = Path(__file__).parents[2] / "logs" / "demo" / "llm-cache"


@pytest.fixture
def logs(tmp_path):
    shutil.copytree(RECORDING, tmp_path / "llm-cache")
    return tmp_path


def demo(logs, *args, **env):
    command = [sys.executable, "-m", "agent.demo", "--no-pause", "--headless", "--logs", str(logs)]
    return subprocess.run(
        [*command, *args],
        capture_output=True,
        text=True,
        timeout=300,
        env={**os.environ, **env},
    )


def test_replay_runs_every_page_as_expected(logs):
    done = demo(logs, "--replay")
    assert done.returncode == 0, done.stdout + done.stderr
    out = done.stdout
    assert "REPLAY of recorded model replies (not live)" in out
    for page, finding in [
        ("order-a", "duplicate_submission"),
        ("order-b", "none"),
        ("signup-a", "data_loss_on_error"),
        ("signup-b", "none"),
    ]:
        row = next(line for line in out.splitlines() if line.startswith(f"{page} "))
        assert "REPLAY" in row and finding in row and row.endswith("as expected")


def test_from_starts_at_that_page(logs):
    done = demo(logs, "--replay", "--from", "signup-a")
    assert done.returncode == 0, done.stdout + done.stderr
    assert "--- order-a" not in done.stdout and "--- signup-b" in done.stdout


def test_live_failure_stops_and_names_the_fallback(logs):
    # Nothing listens on port 9, so every call fails without the network.
    done = demo(logs, LLM_API_KEY="k", LLM_BASE_URL="http://127.0.0.1:9", LLM_PROVIDER="groq")
    assert done.returncode == 1
    assert "LIVE RUN FAILED on order-a" in done.stdout
    assert "Continue with: python -m agent.demo --replay --from order-a" in done.stdout
    assert "--- order-b" not in done.stdout  # it stopped; it did not switch by itself


def test_unknown_start_page(logs):
    done = demo(logs, "--replay", "--from", "nope")
    assert done.returncode == 2 and "order-a, order-b, signup-a, signup-b" in done.stderr


def test_record_cannot_be_a_replay(logs):
    done = demo(logs, "--replay", "--record")
    assert done.returncode == 2 and "--record is a live run" in done.stderr


@pytest.fixture
def answering_api(monkeypatch):
    """The provider, answering every call with one click, without the network."""
    click = {"thought": "t", "action": "click", "ref": "e1", "text": None, "key": None}
    body = json.dumps({"choices": [{"message": {"content": json.dumps(click)}}]}).encode()
    monkeypatch.setattr(llm, "_urllib_post", lambda url, headers, data, timeout: (200, {}, body))
    monkeypatch.setenv("LLM_PROVIDER", "groq")
    monkeypatch.setenv("LLM_API_KEY", "k")


def ask(model):
    obs = Observation(step=0, tree='- button "Send" [ref=e1]', url_path="/x.html")
    return model.next_action("Press Send.", obs, [])


def test_live_run_never_writes_over_the_recording(logs, answering_api):
    # A rehearsal answering differently once overwrote recorded replies and
    # broke the replay of signup-b (14 Oct).
    recorded = {f.name: f.read_bytes() for f in (logs / "llm-cache").iterdir()}
    ask(make_model(replay=False, logs=logs))
    after = {f.name: f.read_bytes() for f in (logs / "llm-cache").iterdir()}
    assert after == recorded
    assert len(list((logs / "live-cache").iterdir())) == 1


def test_record_writes_the_recording(logs, answering_api):
    before = len(list((logs / "llm-cache").iterdir()))
    ask(make_model(replay=False, logs=logs, record=True))
    assert len(list((logs / "llm-cache").iterdir())) == before + 1
    assert not (logs / "live-cache").exists()
