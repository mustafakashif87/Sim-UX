"""Extension axes in a real browser: environment, geometry filters, evidence
logging and the network model (persona catalogue, build steps 1 to 3)."""

import json
import tempfile
from pathlib import Path

import pytest

from agent.fake_model import FakeModel, click
from agent.loop import run
from agent.persona import Persona, load_persona
from agent.tasks import load_tasks, serve


@pytest.fixture(scope="module")
def tasks():
    with serve() as base:
        yield {t.url.rsplit("/", 1)[-1]: t for t in load_tasks(base)}


def entries(result):
    path = result.log_dir / "observations.jsonl"
    return [json.loads(line) for line in path.read_text("utf-8").splitlines()]


def go(browser, task, persona, script):
    page = browser.new_page()
    try:
        return run(page, task, persona, FakeModel(script), Path(tempfile.mkdtemp()), seed=1)
    finally:
        page.close()


def test_low_vision_sees_only_the_viewport_and_logs_evidence(browser, tasks):
    result = go(browser, tasks["order-b.html"], load_persona("low_vision_zoom"), [])
    first = entries(result)[0]
    assert first["page"]["viewport"] == [320, 256]
    assert len(first["observation"]["tree"]) < len(first["full_tree"])  # some is off screen
    assert first["page"]["boxes"]  # geometry is logged for detectors


def test_core_personas_log_no_evidence(browser, tasks):
    result = go(browser, tasks["order-b.html"], load_persona("error_prone"), [])
    assert "full_tree" not in entries(result)[0]


def test_device_environment_uses_a_phone_viewport(browser, tasks):
    data = load_persona("skimmer").model_dump()
    data["environment"] = {"device": "iPhone 13"}
    result = go(browser, tasks["order-b.html"], Persona.model_validate(data), [])
    assert entries(result)[0]["page"]["viewport"] == [390, 664]


def test_slow_network_holds_the_response(browser, tasks):
    data = load_persona("error_prone").model_dump()
    data["perturbation"] = {"seed": 1}
    data["environment"] = {"network": {"latency_ms": 1500}}
    persona = Persona.model_validate(data)
    result = go(browser, tasks["order-b.html"], persona, [click("Place order")])
    # Step 0 sends the order; the answer is held, so the goal is not reached
    # by that click; the run succeeds when the answer arrives, before step 1.
    assert len(result.steps) == 1 and not result.steps[0].goal_reached
    assert result.status == "succeeded"
    assert "Order placed" in entries(result)[-1]["observation"]["tree"]
