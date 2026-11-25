"""A run on pasted HTML (agent.run.execute_own): served offline, no API key."""

import threading

from agent.fake_model import FakeModel, click
from agent.run import execute_own
from agent.tasks import Goal

PAGE = """<!doctype html><title>Shop</title><main><h1>Basket</h1>
<button onclick="document.querySelector('main').innerHTML='<h1>Order placed</h1>'">
Place order</button></main>"""


def test_pasted_html_runs_to_its_goal(tmp_path):
    out = {}

    def go():  # its own thread: execute_own launches its own Playwright
        out["result"], out["findings"] = execute_own(
            "Place the order",
            Goal("heading", "Order placed"),
            FakeModel([click("Place order")]),
            tmp_path,
            condition="baseline",
            html=PAGE,
        )

    t = threading.Thread(target=go)
    t.start()
    t.join(120)
    assert out["result"].status == "succeeded"
