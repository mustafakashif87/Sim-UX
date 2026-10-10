from pathlib import Path

from playwright.sync_api import sync_playwright


def test_page_loads():
    page_path = Path(__file__).parents[2] / "test-app" / "index.html"
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(page_path.resolve().as_uri())
        assert page.title() == "CI switch-on test"
        browser.close()
