"""The keyboard sweep on every test-app page: it reports SB-04 and SB-05 on
their buggy pages and nothing anywhere else (ground truth: SEEDED_BUGS.md)."""

from pathlib import Path

import pytest

from agent.browser import settle
from agent.keyboard_sweep import findings, sweep
from agent.tasks import TEST_APP, load_seeded_bugs, serve

SWEEP_BUGS = {b.buggy: b.signal for b in load_seeded_bugs() if b.detected_by == "keyboard sweep"}
PAGES = sorted(p.name for p in Path(TEST_APP).glob("*.html") if p.name != "success.html")
SIGNALS = {"Tab-cycle trap": "keyboard_trap", "unreachable control": "unreachable_control"}
# Bugs seeded for a persona that the sweep also finds, correctly: B14's size
# picker is divs with click handlers, so no key reaches it either.
ALSO_FOUND = {"size-a.html": ["unreachable_control"]}


@pytest.fixture(scope="module")
def base():
    with serve() as url:
        yield url


def test_ground_truth_names_both_bugs():
    assert set(SWEEP_BUGS) == {"basket-a.html", "booking-a.html"}


@pytest.mark.parametrize("page_name", PAGES)
def test_sweep_matches_ground_truth(browser, base, page_name):
    page = browser.new_page()
    try:
        page.goto(base + page_name)
        settle(page)
        found = [f.signal for f in findings(page_name, sweep(page))]
    finally:
        page.close()
    expected = [SIGNALS[SWEEP_BUGS[page_name]]] if page_name in SWEEP_BUGS else []
    expected += ALSO_FOUND.get(page_name, [])
    assert found == expected
