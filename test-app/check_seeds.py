"""Stand-in for the CI switch-on test: loads a page in Chromium, exits 0."""

import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    page.goto((Path(__file__).parent / "index.html").resolve().as_uri())
    print("title:", page.title())
    browser.close()
sys.exit(0)
