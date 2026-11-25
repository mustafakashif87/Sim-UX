"""SimUX API: start a run, follow its steps as they happen, read its findings.

    uvicorn api.app:app --port 8000        # from the repo root

Endpoints (spec: Delivery, Live interface):

    POST /runs                   {persona, page, condition, seed} -> 202 {run_id, status};
                                 or, for the user's own page, {html} or {url} in place of
                                 page, with {task, goal_role, goal_name}
    GET  /runs/{run_id}          status, run.json, step records and findings
    GET  /runs/{run_id}/stream   server-sent events: one `step` per StepRecord as the
                                 loop writes it, then one `end` with status and findings
    GET  /options                personas, pages and conditions a client may choose
    GET  /health

The API holds the LLM key (`LLM_*` variables or the repo's `.env`); the browser
never sees it. Each run drives a real Chromium, so runs go through a small
worker pool (`SIMUX_WORKERS`, default 1) and a short queue (`SIMUX_MAX_QUEUED`,
default 5); a full queue answers 429 rather than spending model calls. Logs go
to `SIMUX_LOGS` (default `logs/api/`), so a finished run can still be read
after a restart. Allowed browser origins: `SIMUX_CORS_ORIGINS`, comma-separated.
Pasted HTML runs offline; URL runs need `SIMUX_ALLOW_URLS=1`, since the
server's browser then opens pages the client names.

Nothing here imports Playwright at load time: the browser side is imported by
the runner when a run starts, so the unit tests need no browser.
"""

import asyncio
import json
import os
import threading
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator, model_validator

from agent.detectors import audit
from agent.ids import is_run_id, new_run_id
from agent.perception import FILTERS, Box, View
from agent.persona import CONDITIONS, PERSONAS_DIR, Persona, for_condition, load_persona
from agent.report import explain
from agent.tasks import check_public_url, load_entries

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_LOGS = ROOT / "logs" / "api"
DEFAULT_ORIGINS = "http://localhost:5173,http://127.0.0.1:5173"

# What the loop writes to run.json when it ends (agent.loop.RunStatus), plus
# `failed` for a run that broke before the loop could log anything.
ENDED = {"succeeded", "gave_up", "step_cap", "aborted_provider", "crashed", "failed"}
POLL_SECONDS = 0.25
MAX_HTML_CHARS = 500_000
KEEPALIVE_SECONDS = 15.0


class RunRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    persona: str = "error_prone"
    page: str | None = Field(default=None, description="test-app page without .html, e.g. order-a")
    condition: Literal["persona", "baseline"] = "persona"
    seed: int | None = Field(default=None, ge=0, description="perturbation seed")
    # The user's own page, in place of `page`: pasted HTML or a public URL,
    # the task to attempt, and the element that shows it is done.
    html: str | None = Field(default=None, max_length=MAX_HTML_CHARS)
    url: str | None = Field(default=None, max_length=2000)
    task: str | None = Field(default=None, max_length=500)
    goal_role: str = Field(default="heading", pattern=r"^[a-z]+$")
    goal_name: str | None = Field(default=None, max_length=200)

    @field_validator("page")
    @classmethod
    def _no_extension(cls, page: str | None) -> str | None:
        return page.removesuffix(".html") if page else page

    @model_validator(mode="after")
    def _one_source(self) -> "RunRequest":
        given = [k for k in ("page", "html", "url") if getattr(self, k)]
        if len(given) != 1:
            raise ValueError("give exactly one of page, html and url")
        if given[0] != "page" and not (self.task and self.goal_name):
            raise ValueError("an own page needs a task and a goal_name")
        return self


# Runs one request to the end, writing its log under `<logs>/<run_id>/`.
Runner = Callable[[RunRequest, str, Path], None]


def live_runner(req: RunRequest, run_id: str, logs: Path) -> None:
    """The real thing: the LLM client from the environment and a real Chromium."""
    from agent.llm import LLMClient
    from agent.run import execute

    model = LLMClient.from_env(cache_dir=logs / "llm-cache")
    if req.page:
        execute(
            req.page, req.seed, model, logs, req.persona, condition=req.condition, run_id=run_id
        )
        return
    from agent.run import execute_own
    from agent.tasks import Goal

    goal = Goal(req.goal_role, req.goal_name)
    execute_own(
        req.task, goal, model, logs, req.persona, req.seed, req.condition, run_id, req.html, req.url
    )


def pages() -> dict[str, dict]:
    """Each test-app page and the task run on it, by page name without .html."""
    return {
        name.removesuffix(".html"): {"task": e.id, "text": e.text}
        for e in load_entries()
        for name in e.pages
    }


def unbuilt_filter(persona: Persona) -> str | None:
    """Why this persona cannot run yet (a perception filter not built), or None."""
    for name in persona.perception.filters:
        try:
            FILTERS[name]([], View(viewport=Box(0, 0, 1, 1)))
        except NotImplementedError as e:
            return str(e)
    return None


def personas() -> list[dict]:
    out = []
    for path in sorted(PERSONAS_DIR.glob("*.yaml")):
        p = load_persona(path)
        reason = unbuilt_filter(p)
        out.append(
            {
                "id": p.id,
                "max_steps": p.memory.max_steps,
                "history_turns": p.memory.history_turns,
                "built": reason is None,
                "reason": reason,
            }
        )
    return out


@dataclass
class Job:
    run_id: str
    request: RunRequest
    state: Literal["queued", "running", "finished", "failed"] = "queued"
    error: str | None = None


class Busy(Exception):
    pass


class Runs:
    """Jobs started by this process, and the log folders every run leaves."""

    def __init__(self, logs: Path, runner: Runner, workers: int = 1, max_queued: int = 5):
        self.logs = logs
        self._runner = runner
        self._workers = workers
        self._max_queued = max_queued
        self._pool = ThreadPoolExecutor(workers, thread_name_prefix="simux-run")
        self._jobs: dict[str, Job] = {}
        self._findings: dict[str, list[dict]] = {}
        self._lock = threading.Lock()

    def start(self, req: RunRequest) -> Job:
        with self._lock:
            waiting = sum(j.state in ("queued", "running") for j in self._jobs.values())
            if waiting >= self._workers + self._max_queued:
                raise Busy(f"{waiting} runs are already queued or running")
            job = Job(new_run_id(req.persona), req)
            self._jobs[job.run_id] = job
        self._pool.submit(self._work, job)
        return job

    def _work(self, job: Job) -> None:
        job.state = "running"
        try:
            self._runner(job.request, job.run_id, self.logs)
            job.state = "finished"
        except (Exception, SystemExit) as e:  # execute() exits on an unknown page
            job.state = "failed"
            job.error = f"{type(e).__name__}: {e}"

    def job(self, run_id: str) -> Job | None:
        return self._jobs.get(run_id)

    def log_dir(self, run_id: str) -> Path:
        return self.logs / run_id

    def meta(self, run_id: str) -> dict | None:
        path = self.log_dir(run_id) / "run.json"
        if not path.exists():
            return None
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:  # caught mid-write
            return None

    def status(self, run_id: str) -> str | None:
        """queued, running, a RunStatus from run.json, or failed; None if unknown."""
        meta = self.meta(run_id)
        job = self.job(run_id)
        if meta is not None and "status" in meta:
            # run.json is written before the runner returns; report it once the
            # job is done, so findings are ready when the status says ended.
            if job is None or job.state in ("finished", "failed"):
                return meta["status"]
            return "running"
        if job is not None:
            return job.state if job.state != "finished" else "failed"
        return "failed" if self.log_dir(run_id).is_dir() else None

    def steps(self, run_id: str) -> list[dict]:
        """Step records written so far: whole lines only, as the loop flushes each."""
        path = self.log_dir(run_id) / "steps.jsonl"
        if not path.exists():
            return []
        text = path.read_text(encoding="utf-8")
        return [json.loads(line) for line in text.split("\n")[:-1] if line]

    def findings(self, run_id: str) -> list[dict]:
        if run_id not in self._findings:
            log_dir = self.log_dir(run_id)
            self._findings[run_id] = explain(audit(log_dir), log_dir)
        return self._findings[run_id]

    def snapshot(self, run_id: str) -> dict:
        status = self.status(run_id)
        job = self.job(run_id)
        ended_with_log = status in ENDED and self.meta(run_id) is not None
        return {
            "run_id": run_id,
            "status": status,
            "request": _echo(job.request) if job else None,
            "error": job.error if job else None,
            "meta": self.meta(run_id),
            "steps": self.steps(run_id),
            "findings": self.findings(run_id) if ended_with_log else [],
        }


OWN_PAGE_FIELDS = {"url", "task", "goal_role", "goal_name"}


def _echo(req: RunRequest) -> dict:
    """The request as a client may read it back: never the pasted HTML, and
    for a test-app page only the fields that apply."""
    return req.model_dump(exclude={"html"} | (OWN_PAGE_FIELDS if req.page else set()))


def urls_allowed() -> bool:
    return os.environ.get("SIMUX_ALLOW_URLS") == "1"


def _event(name: str, data: dict | str) -> str:
    body = data if isinstance(data, str) else json.dumps(data)
    return f"event: {name}\ndata: {body}\n\n"


def create_app(
    runner: Runner = live_runner,
    logs: Path | None = None,
    workers: int | None = None,
    max_queued: int | None = None,
    cors_origins: list[str] | None = None,
) -> FastAPI:
    logs = logs or Path(os.environ.get("SIMUX_LOGS", DEFAULT_LOGS))
    workers = workers or int(os.environ.get("SIMUX_WORKERS", "1"))
    if max_queued is None:
        max_queued = int(os.environ.get("SIMUX_MAX_QUEUED", "5"))
    if cors_origins is None:
        raw = os.environ.get("SIMUX_CORS_ORIGINS", DEFAULT_ORIGINS)
        cors_origins = [o.strip() for o in raw.split(",") if o.strip()]

    logs.mkdir(parents=True, exist_ok=True)
    runs = Runs(logs, runner, workers, max_queued)
    app = FastAPI(title="SimUX API", version="0.2.0")
    app.state.runs = runs
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type"],
    )

    def known(run_id: str) -> None:
        if not is_run_id(run_id) or runs.status(run_id) is None:
            raise HTTPException(404, f"no run {run_id!r}")

    @app.get("/health")
    def health() -> dict:
        return {"status": "ok"}

    @app.get("/options")
    def options() -> dict:
        return {
            "personas": personas(),
            "pages": [{"page": name, **info} for name, info in pages().items()],
            "conditions": list(CONDITIONS),
            "own_page": {"html": True, "url": urls_allowed()},
        }

    @app.post("/runs", status_code=202)
    def start_run(req: RunRequest) -> dict:
        try:
            persona = for_condition(load_persona(req.persona), req.condition)
        except (FileNotFoundError, ValueError, ValidationError):
            raise HTTPException(422, f"unknown persona {req.persona!r}") from None
        reason = unbuilt_filter(persona)
        if reason:
            raise HTTPException(422, f"persona {req.persona!r} cannot run yet: {reason}")
        if req.page and req.page not in pages():
            raise HTTPException(422, f"no task for page {req.page!r}")
        if req.url:
            if not urls_allowed():
                raise HTTPException(422, "URL runs are off on this server; paste the HTML instead")
            try:
                check_public_url(req.url)
            except ValueError as e:
                raise HTTPException(422, str(e)) from None
        try:
            job = runs.start(req)
        except Busy as e:
            raise HTTPException(429, str(e)) from None
        return {"run_id": job.run_id, "status": job.state}

    @app.get("/runs/{run_id}")
    def get_run(run_id: str) -> dict:
        known(run_id)
        return runs.snapshot(run_id)

    @app.get("/runs/{run_id}/stream")
    async def stream_run(run_id: str, request: Request) -> StreamingResponse:
        known(run_id)

        async def events():
            sent = 0
            idle = 0.0
            while True:
                status = runs.status(run_id)
                steps = runs.steps(run_id)
                for step in steps[sent:]:
                    yield _event("step", step)
                    idle = 0.0
                sent = len(steps)
                if status in ENDED:
                    snap = await asyncio.to_thread(runs.snapshot, run_id)
                    end = {k: snap[k] for k in ("status", "error", "findings")}
                    yield _event("end", end)
                    return
                if await request.is_disconnected():
                    return
                await asyncio.sleep(POLL_SECONDS)
                idle += POLL_SECONDS
                if idle >= KEEPALIVE_SECONDS:
                    yield ": keep-alive\n\n"
                    idle = 0.0

        headers = {"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}
        return StreamingResponse(events(), media_type="text/event-stream", headers=headers)

    return app


app = create_app()
