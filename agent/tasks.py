"""Tasks from the test app, and a local server to run them on.

`test-app/tasks.yaml` (owned by the test-app author) lists one task per
buggy/clean page pair. `load_tasks` turns each entry into one `Task` per page;
the loop imports `Task` from here, so this module needs no browser. The pages
submit with `fetch` to relative URLs, which browsers block on `file://`, so
runs need them over HTTP: `serve` gives a local server, or pass the deployed
site's URL as the base.

    with serve(TEST_APP) as base:
        for task in load_tasks(base):
            run(page, task, persona, model, logs)
"""

import functools
import http.server
import threading
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urljoin

import yaml
from pydantic import ConfigDict, Field

from agent.contracts import Contract

TEST_APP = Path(__file__).resolve().parents[1] / "test-app"


@dataclass(frozen=True)
class Goal:
    """Harness-side success check: a visible element with this role and name."""

    role: str
    name: str


@dataclass(frozen=True)
class Task:
    id: str
    url: str
    text: str  # what the user wants, as the model reads it; never names a bug
    goal: Goal
    # URL glob of the form's submission endpoint, e.g. "**/api/orders". The
    # harness answers it with 200, so a run does not depend on where the page
    # is hosted (GitHub Pages rejects POSTs). Submissions are logged either way.
    endpoint: str | None = None


class _Goal(Contract):
    role: str
    name: str


class TaskEntry(Contract):
    """One entry of tasks.yaml: a task shared by both pages of a pair."""

    model_config = ConfigDict(strict=True)

    id: str = Field(pattern=r"^[a-z][a-z0-9_-]*$")
    pages: list[str] = Field(min_length=1)
    text: str = Field(min_length=1)
    goal: _Goal
    endpoint: str | None = None


def load_entries(path: Path = TEST_APP / "tasks.yaml") -> list[TaskEntry]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError(f"{path.name}: expected a list of tasks")
    entries = [TaskEntry.model_validate(e) for e in data]
    ids = [e.id for e in entries]
    if len(ids) != len(set(ids)):
        raise ValueError(f"{path.name}: duplicate task ids")
    return entries


def load_tasks(base_url: str, path: Path = TEST_APP / "tasks.yaml") -> list[Task]:
    """One Task per page in tasks.yaml, its URL built on `base_url`."""
    base = base_url if base_url.endswith("/") else base_url + "/"
    return [
        Task(
            id=entry.id,
            url=urljoin(base, page),
            text=entry.text,
            goal=Goal(entry.goal.role, entry.goal.name),
            endpoint=entry.endpoint,
        )
        for entry in load_entries(path)
        for page in entry.pages
    ]


@dataclass(frozen=True)
class SeededBug:
    """One row of the Bugs table in SEEDED_BUGS.md, the single ground truth."""

    id: str
    buggy: str
    clean: str
    detected_by: str  # e.g. "P1 Error-prone", "axe-core", "keyboard sweep"
    signal: str | None  # None when no detector exists yet ("none yet")


_BUG_COLUMNS = ("ID", "Buggy page", "Clean page", "Detected by", "Expected signal")


def load_seeded_bugs(path: Path = TEST_APP / "SEEDED_BUGS.md") -> list[SeededBug]:
    """Rows of the first table under "## Bugs" in SEEDED_BUGS.md."""
    lines = path.read_text(encoding="utf-8").splitlines()
    headings = [i for i, line in enumerate(lines) if line.strip() == "## Bugs"]
    if not headings:
        raise ValueError(f"{path.name}: no '## Bugs' section")
    start = headings[0]
    table = []
    for line in lines[start + 1 :]:
        if line.startswith("|"):
            table.append([c.strip().strip("`") for c in line.strip().strip("|").split("|")])
        elif table:
            break  # the table has ended
    header, rows = table[0], table[2:]  # table[1] is the --- separator
    col = {name: header.index(name) for name in _BUG_COLUMNS}
    bugs = []
    for row in rows:
        signal = row[col["Expected signal"]]
        bugs.append(
            SeededBug(
                id=row[col["ID"]],
                buggy=row[col["Buggy page"]],
                clean=row[col["Clean page"]],
                detected_by=row[col["Detected by"]],
                signal=None if signal.lower().startswith("none") else signal,
            )
        )
    return bugs


class _QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args) -> None:
        pass


@contextmanager
def serve(directory: Path = TEST_APP) -> Iterator[str]:
    """Serve `directory` on a free local port; yields its base URL."""
    handler = functools.partial(_QuietHandler, directory=str(directory))
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}/"
    finally:
        server.shutdown()
        server.server_close()
