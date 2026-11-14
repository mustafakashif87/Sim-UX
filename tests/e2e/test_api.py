"""The API contract with the real loop, a real Chromium and the scripted model.

Each run executes in the API's worker thread and launches its own Chromium,
as `live_runner` does in production; only the model is scripted.
"""

import json
import time

import pytest

pytest.importorskip("fastapi", reason='needs pip install -e ".[dev,browser,api]"')

from fastapi.testclient import TestClient  # noqa: E402

from agent.fake_model import FakeModel, click  # noqa: E402
from agent.run import execute  # noqa: E402
from api.app import RunRequest, create_app  # noqa: E402


def scripted(req: RunRequest, run_id: str, logs) -> None:
    model = FakeModel([click("Place order")])
    execute(req.page, req.seed, model, logs, req.persona, condition=req.condition, run_id=run_id)


@pytest.fixture
def api(tmp_path):
    return TestClient(create_app(runner=scripted, logs=tmp_path))


def ended(api: TestClient, run_id: str, timeout=60.0) -> dict:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        body = api.get(f"/runs/{run_id}").json()
        if body["status"] not in ("queued", "running"):
            return body
        time.sleep(0.2)
    raise AssertionError("run did not end")


def test_buggy_page_finding_with_citations(api):
    # Seed 1 doubles P1's first click: order-a takes both orders.
    run_id = api.post("/runs", json={"page": "order-a", "seed": 1}).json()["run_id"]
    body = ended(api, run_id)
    assert body["status"] == "succeeded", body["error"]
    assert body["meta"]["run_id"] == run_id and body["meta"]["condition"] == "persona"
    assert body["steps"][0]["perturbation"] == "double_submit"
    (finding,) = body["findings"]
    assert finding["signal"] == "duplicate_submission" and finding["citations"]


def test_baseline_on_the_same_page_and_seed_finds_nothing(api):
    request = {"page": "order-a", "seed": 1, "condition": "baseline"}
    run_id = api.post("/runs", json=request).json()["run_id"]
    body = ended(api, run_id)
    assert body["status"] == "succeeded" and body["findings"] == []
    assert body["steps"][0]["perturbation"] is None


def test_stream_follows_a_live_run(api):
    run_id = api.post("/runs", json={"page": "order-b", "seed": 1}).json()["run_id"]
    with api.stream("GET", f"/runs/{run_id}/stream") as response:
        text = response.read().decode()
    names = [
        line.removeprefix("event: ") for line in text.splitlines() if line.startswith("event:")
    ]
    assert names == ["step", "end"]
    end = json.loads(text.rsplit("data: ", 1)[1])
    assert end["status"] == "succeeded" and end["findings"] == []
