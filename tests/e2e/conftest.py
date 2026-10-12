import http.server
import threading
import time
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


class _SlowHandler(http.server.BaseHTTPRequestHandler):
    """Answers every POST after SLOW_MS, like a real server under load."""

    def do_POST(self):
        time.sleep(SLOW_MS / 1000)
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(b"Sent")

    def log_message(self, *args):
        pass


SLOW_MS = 400


@pytest.fixture(scope="session")
def slow_endpoint():
    """URL of a local endpoint that takes SLOW_MS to answer."""
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), _SlowHandler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{server.server_port}/api/send"
    server.shutdown()
