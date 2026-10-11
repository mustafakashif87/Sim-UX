from pathlib import Path

import pytest
from playwright.sync_api import sync_playwright

FIXTURE_PAGES = Path(__file__).parents[1] / "fixtures" / "pages"


@pytest.fixture(scope="session")
def browser():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        yield browser
        browser.close()


@pytest.fixture
def open_fixture(browser):
    """Open a page from tests/fixtures/pages by file name."""
    pages = []

    def _open(name: str):
        page = browser.new_page()
        page.goto((FIXTURE_PAGES / name).resolve().as_uri())
        pages.append(page)
        return page

    yield _open
    for page in pages:
        page.close()
