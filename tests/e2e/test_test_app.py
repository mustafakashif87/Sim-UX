"""P1 and its detectors on the real seeded test app (test-app/), served over HTTP.

Which page is buggy comes from SEEDED_BUGS.md and each task from tasks.yaml,
so this test follows the test-app author's ground truth rather than copying
it. If a page changes so that a detector no longer fires on its buggy page,
or fires on its clean one, this fails.
"""

import tempfile
from pathlib import Path

import pytest

from agent.detectors import detect, load_run
from agent.fake_model import FakeModel, click, type_into
from agent.loop import run
from agent.persona import Persona, load_persona
from agent.tasks import load_seeded_bugs, load_tasks, serve

BUGS = {b.id: b for b in load_seeded_bugs()}


@pytest.fixture(scope="module")
def tasks():
    with serve() as base:
        yield {t.url.rsplit("/", 1)[-1]: t for t in load_tasks(base)}


def p1(**rates):
    data = load_persona("error_prone").model_dump()
    data["perturbation"] = {"seed": 1, **rates}
    return Persona.model_validate(data)


def findings(browser, task, persona, script):
    page = browser.new_page()
    try:
        result = run(page, task, persona, FakeModel(script), Path(tempfile.mkdtemp()))
    finally:
        page.close()
    return [f.signal for f in detect(load_run(result.log_dir))], result


# The mistake each bug needs, as P1 would make it, and a script that reaches it.
SCENARIOS = {
    "B1": (  # a mistyped email: no @
        p1(),
        [
            type_into("Full name", "Sam Khan"),
            type_into("Email address", "sam.khan.example.com"),
            click("Create account"),
        ],
    ),
    "B4": (p1(double_submit_rate=1.0), [click("Place order")]),  # a double press
}


@pytest.mark.parametrize("bug_id", SCENARIOS)
@pytest.mark.parametrize("version", ["buggy", "clean"])
def test_detector_fires_on_buggy_only(browser, tasks, bug_id, version):
    bug = BUGS[bug_id]
    persona, script = SCENARIOS[bug_id]
    page = bug.buggy if version == "buggy" else bug.clean
    found, _ = findings(browser, tasks[page], persona, script)
    assert (bug.signal in found) == (version == "buggy"), found


@pytest.mark.parametrize("page", ["signup-a.html", "signup-b.html"])
def test_careful_user_succeeds_without_findings(browser, tasks, page):
    script = [
        type_into("Full name", "Sam Khan"),
        type_into("Email address", "sam.khan@example.com"),
        click("Create account"),
    ]
    found, result = findings(browser, tasks[page], p1(), script)
    assert result.status == "succeeded" and found == []
