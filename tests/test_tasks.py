import urllib.request

import pytest
import yaml
from pydantic import ValidationError

from agent.tasks import TEST_APP, load_entries, load_seeded_bugs, load_tasks, serve
from grounding import default_signal_map

PAGES_URL = "https://mustafakashif87.github.io/Sim-UX"


class TestTasksYaml:
    """The real test-app/tasks.yaml, owned by the test-app author."""

    def test_every_page_exists(self):
        for entry in load_entries():
            for page in entry.pages:
                assert (TEST_APP / page).is_file(), page

    def test_one_task_per_page(self):
        entries = load_entries()
        tasks = load_tasks(PAGES_URL)
        assert len(tasks) == sum(len(e.pages) for e in entries)
        assert tasks[0].url == f"{PAGES_URL}/{entries[0].pages[0]}"
        assert tasks[0].goal.role and tasks[0].goal.name

    def test_every_persona_bug_page_has_a_task(self):
        pages = {t.url.rsplit("/", 1)[-1] for t in load_tasks(PAGES_URL)}
        persona_bugs = [b for b in load_seeded_bugs() if b.detected_by[:2] in ("P1", "P2", "P3")]
        assert {b.id for b in persona_bugs} >= {f"B{i}" for i in range(1, 13)}
        for bug in persona_bugs:
            assert {bug.buggy, bug.clean} <= pages, bug.id

    def test_both_pages_of_a_pair_share_one_task(self):
        by_page = {page: e.id for e in load_entries() for page in e.pages}
        for bug in load_seeded_bugs():
            if bug.buggy in by_page:
                assert by_page[bug.buggy] == by_page.get(bug.clean), bug.id

    @pytest.mark.parametrize("base", [PAGES_URL, PAGES_URL + "/"])
    def test_base_url_with_or_without_slash(self, base):
        assert load_tasks(base)[0].url.startswith(PAGES_URL + "/") and "//" not in (
            load_tasks(base)[0].url.removeprefix("https://")
        )


def write(tmp_path, data):
    path = tmp_path / "tasks.yaml"
    path.write_text(yaml.safe_dump(data))
    return path


GOOD = {
    "id": "order",
    "pages": ["order-a.html"],
    "text": "Place the order",
    "goal": {"role": "heading", "name": "Order placed"},
    "endpoint": "**/api/orders",
}


class TestRejected:
    @pytest.mark.parametrize(
        "change",
        [
            lambda e: e.update(hint="the button stays enabled"),  # unknown key
            lambda e: e.pop("goal"),
            lambda e: e.update(pages=[]),
            lambda e: e.update(text=""),
            lambda e: e["goal"].update(selector="#result"),
            lambda e: e.update(id="Order Page"),
        ],
    )
    def test_invalid_entry(self, tmp_path, change):
        entry = {**GOOD, "goal": dict(GOOD["goal"])}
        change(entry)
        with pytest.raises(ValidationError):
            load_entries(write(tmp_path, [entry]))

    def test_duplicate_ids(self, tmp_path):
        with pytest.raises(ValueError, match="duplicate"):
            load_entries(write(tmp_path, [GOOD, GOOD]))

    def test_not_a_list(self, tmp_path):
        with pytest.raises(ValueError, match="list"):
            load_entries(write(tmp_path, GOOD))

    def test_endpoint_is_optional(self, tmp_path):
        entry = {k: v for k, v in GOOD.items() if k != "endpoint"}
        assert load_entries(write(tmp_path, [entry]))[0].endpoint is None


class TestSeededBugs:
    def test_reads_the_bugs_table(self):
        bugs = {b.id: b for b in load_seeded_bugs()}
        assert bugs["B1"].buggy.endswith(".html") and bugs["B1"].clean.endswith(".html")
        assert bugs["B1"].signal == "data_loss_on_error"
        assert bugs["B4"].signal == "duplicate_submission"
        assert all(b.buggy != b.clean for b in bugs.values())

    def test_every_expected_persona_signal_is_mapped(self):
        # The signal each persona bug should produce has candidate criteria in
        # grounding/signal_map.yaml, so its finding can be grounded.
        signals = default_signal_map()
        for bug in load_seeded_bugs():
            if bug.detected_by[:2] in ("P1", "P2", "P3") and bug.signal:
                assert bug.signal in signals, bug.id

    def test_no_detector_yet_is_none(self, tmp_path):
        md = tmp_path / "SEEDED_BUGS.md"
        md.write_text(
            "# Ground truth\n\n## Bugs\n\n"
            "| ID | Buggy page | Clean page | Detected by | Expected signal | Bug |\n"
            "| --- | --- | --- | --- | --- | --- |\n"
            "| B6 | `x-a.html` | `x-b.html` | P1 Error-prone | none yet (see note) | asks again |\n"
            "\nSome text.\n\n| Other | table |\n| --- | --- |\n| a | b |\n"
        )
        (bug,) = load_seeded_bugs(md)
        assert (bug.id, bug.buggy, bug.signal) == ("B6", "x-a.html", None)

    def test_missing_bugs_section(self, tmp_path):
        md = tmp_path / "SEEDED_BUGS.md"
        md.write_text("# Ground truth\n\nNo table here.\n")
        with pytest.raises(ValueError, match="Bugs"):
            load_seeded_bugs(md)


def test_serve_gives_the_test_app_over_http():
    with serve() as base:
        with urllib.request.urlopen(base + "index.html") as response:
            assert response.status == 200
            assert b"<title>" in response.read()
