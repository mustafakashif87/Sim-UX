"""The API on fake runners that write a run's log files: no browser, no model.

The same endpoints with the real loop, Chromium and the scripted model are in
tests/e2e/test_api.py.
"""

import json
import threading
import time

import pytest

pytest.importorskip("fastapi", reason='needs pip install -e ".[dev,api]"')

from fastapi.testclient import TestClient  # noqa: E402

from agent.contracts import Action, Observation, StepRecord  # noqa: E402
from agent.ids import is_run_id  # noqa: E402
from api.app import RunRequest, create_app  # noqa: E402

PLACE_ORDER = Action(thought="", action="click", ref="e3")
TREE = '- heading "Your basket" [level=1] [ref=e1]\n- button "Place order" [ref=e3]'


def write_run(req: RunRequest, run_id: str, logs, *, steps=1, double=True, pause=0.0):
    """A finished run in the loop's layout. `double` logs two identical orders
    from step 0, which duplicate_submission reports."""
    log_dir = logs / run_id
    log_dir.mkdir(parents=True)
    with open(log_dir / "steps.jsonl", "a", encoding="utf-8") as f:
        for step in range(steps):
            time.sleep(pause)
            record = StepRecord(
                run_id=run_id,
                persona=req.persona,
                page=f"{req.page}.html",
                step=step,
                observation_hash="h",
                intended_action=PLACE_ORDER,
                executed_action=PLACE_ORDER,
                perturbation="double_submit" if double and step == 0 else None,
                result="ok",
                goal_reached=step == steps - 1,
            )
            f.write(record.model_dump_json() + "\n")
            f.flush()
    observations = [Observation(step=i, tree=TREE, url_path="/order.html") for i in range(steps)]
    (log_dir / "observations.jsonl").write_text(
        "".join(
            json.dumps({"step": o.step, "observation": o.model_dump()}) + "\n" for o in observations
        ),
        encoding="utf-8",
    )
    order = {"step": 0, "method": "POST", "url": "http://x/api/order", "body": "kettle"}
    (log_dir / "network.jsonl").write_text(
        (json.dumps(order) + "\n") * (2 if double else 1), encoding="utf-8"
    )
    meta = {
        "run_id": run_id,
        "persona": req.persona,
        "condition": req.condition,
        "page": f"{req.page}.html",
        "seed": req.seed,
        "status": "succeeded",
        "steps": steps,
    }
    (log_dir / "run.json").write_text(json.dumps(meta), encoding="utf-8")


def client(tmp_path, runner=write_run, **kwargs) -> TestClient:
    return TestClient(create_app(runner=runner, logs=tmp_path, **kwargs))


def wait_until_ended(c: TestClient, run_id: str, timeout=10.0) -> dict:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        body = c.get(f"/runs/{run_id}").json()
        if body["status"] not in ("queued", "running"):
            return body
        time.sleep(0.02)
    raise AssertionError(f"run {run_id} did not end")


def test_health(tmp_path):
    assert client(tmp_path).get("/health").json() == {"status": "ok"}


def test_options_list_personas_pages_and_conditions(tmp_path):
    body = client(tmp_path).get("/options").json()
    built = {p["id"]: p["built"] for p in body["personas"]}
    assert built["error_prone"] is True and built["low_literacy"] is False
    pages = {p["page"]: p for p in body["pages"]}
    assert {"order-a", "order-b", "signup-a"} <= set(pages)
    assert pages["order-a"]["task"] == pages["order-b"]["task"]
    assert body["conditions"] == ["persona", "baseline"]


def test_a_run_from_start_to_findings(tmp_path):
    c = client(tmp_path)
    started = c.post("/runs", json={"page": "order-a", "seed": 1})
    assert started.status_code == 202
    run_id = started.json()["run_id"]
    assert is_run_id(run_id) and "error_prone" in run_id

    body = wait_until_ended(c, run_id)
    assert body["status"] == "succeeded"
    assert body["request"] == {
        "persona": "error_prone",
        "page": "order-a",
        "condition": "persona",
        "seed": 1,
    }
    assert [s["step"] for s in body["steps"]] == [0]
    assert body["steps"][0]["perturbation"] == "double_submit"
    (finding,) = body["findings"]
    assert finding["signal"] == "duplicate_submission"
    assert {c["criterion_id"] for c in finding["citations"]} == {"Nielsen 5", "WCAG 3.3.4"}


def test_page_may_carry_its_extension(tmp_path):
    c = client(tmp_path)
    run_id = c.post("/runs", json={"page": "order-b.html"}).json()["run_id"]
    assert wait_until_ended(c, run_id)["request"]["page"] == "order-b"


def test_clean_run_has_no_findings(tmp_path):
    def clean(req, run_id, logs):
        write_run(req, run_id, logs, double=False)

    c = client(tmp_path, runner=clean)
    run_id = c.post("/runs", json={"page": "order-b", "condition": "baseline"}).json()["run_id"]
    body = wait_until_ended(c, run_id)
    assert body["findings"] == [] and body["meta"]["condition"] == "baseline"


@pytest.mark.parametrize(
    "payload, message",
    [
        ({"page": "order-a", "persona": "keyboard"}, "unknown persona"),
        ({"page": "order-a", "persona": "../secrets"}, "unknown persona"),
        ({"page": "no-such-page"}, "no task for page"),
        ({"page": "order-a", "persona": "low_literacy"}, "cannot run yet"),
    ],
)
def test_rejected_requests_say_why(tmp_path, payload, message):
    response = client(tmp_path).post("/runs", json=payload)
    assert response.status_code == 422 and message in response.json()["detail"]


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"page": "order-a", "condition": "clean"},
        {"page": "order-a", "seed": -1},
        {"page": "order-a", "temperature": 1},
    ],
)
def test_malformed_requests(tmp_path, payload):
    assert client(tmp_path).post("/runs", json=payload).status_code == 422


def test_unbuilt_persona_runs_as_baseline(tmp_path):
    # The baseline uses the full tree, so P3's missing filter does not apply.
    c = client(tmp_path)
    response = c.post(
        "/runs", json={"page": "order-a", "persona": "low_literacy", "condition": "baseline"}
    )
    assert response.status_code == 202


@pytest.mark.parametrize("run_id", ["nope", "..", "20261114T000000Z-error_prone-abcdef"])
def test_unknown_run(tmp_path, run_id):
    c = client(tmp_path)
    assert c.get(f"/runs/{run_id}").status_code == 404
    assert c.get(f"/runs/{run_id}/stream").status_code == 404


def test_a_crash_outside_the_loop_is_reported(tmp_path):
    def broken(req, run_id, logs):
        raise RuntimeError("LLM_API_KEY is not set")

    c = client(tmp_path, runner=broken)
    run_id = c.post("/runs", json={"page": "order-a"}).json()["run_id"]
    body = wait_until_ended(c, run_id)
    assert body["status"] == "failed" and "LLM_API_KEY" in body["error"]
    assert body["findings"] == []


def test_full_queue_answers_429(tmp_path):
    release = threading.Event()

    def blocked(req, run_id, logs):
        release.wait(5)

    c = client(tmp_path, runner=blocked, workers=1, max_queued=1)
    try:
        assert c.post("/runs", json={"page": "order-a"}).status_code == 202
        assert c.post("/runs", json={"page": "order-a"}).status_code == 202
        assert c.post("/runs", json={"page": "order-a"}).status_code == 429
    finally:
        release.set()


def test_finished_run_is_readable_after_a_restart(tmp_path):
    first = client(tmp_path)
    run_id = first.post("/runs", json={"page": "order-a"}).json()["run_id"]
    wait_until_ended(first, run_id)
    body = client(tmp_path).get(f"/runs/{run_id}").json()  # a new app, same logs
    assert body["status"] == "succeeded" and body["request"] is None
    assert body["findings"][0]["signal"] == "duplicate_submission"


def events(text: str) -> list[tuple[str, dict]]:
    out = []
    for block in text.split("\n\n"):
        lines = dict(line.split(": ", 1) for line in block.splitlines() if not line.startswith(":"))
        if "event" in lines:
            out.append((lines["event"], json.loads(lines["data"])))
    return out


def test_stream_sends_each_step_then_the_end(tmp_path):
    def slow(req, run_id, logs):
        write_run(req, run_id, logs, steps=3, pause=0.1)

    c = client(tmp_path, runner=slow)
    run_id = c.post("/runs", json={"page": "order-a"}).json()["run_id"]
    with c.stream("GET", f"/runs/{run_id}/stream") as response:
        assert response.headers["content-type"].startswith("text/event-stream")
        got = events(response.read().decode())
    assert [name for name, _ in got] == ["step", "step", "step", "end"]
    assert [data["step"] for _, data in got[:3]] == [0, 1, 2]
    end = got[-1][1]
    assert end["status"] == "succeeded" and end["findings"][0]["signal"] == "duplicate_submission"


def test_stream_of_an_ended_run_replays_it(tmp_path):
    c = client(tmp_path)
    run_id = c.post("/runs", json={"page": "order-a"}).json()["run_id"]
    wait_until_ended(c, run_id)
    with c.stream("GET", f"/runs/{run_id}/stream") as response:
        got = events(response.read().decode())
    assert [name for name, _ in got] == ["step", "end"]


def test_cors_allows_the_configured_origin_only(tmp_path):
    c = client(tmp_path, cors_origins=["https://simux.example"])
    ok = c.get("/health", headers={"Origin": "https://simux.example"})
    assert ok.headers.get("access-control-allow-origin") == "https://simux.example"
    other = c.get("/health", headers={"Origin": "https://evil.example"})
    assert "access-control-allow-origin" not in other.headers
