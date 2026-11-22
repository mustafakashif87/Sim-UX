"""Environment axis: what the world does to the user (persona catalogue,
Framework changes). P6, P7, P8 and P10 use it; P1 to P3 leave it at its
defaults, so their runs are unchanged.

- `device`: a phone or tablet: viewport, pixel ratio, touch and user agent,
  in a browser context the run opens and closes itself.
- `viewport`: the visible area in CSS px (P7's 320x256 is 1280x1024 at 400%).
- `text_scale`: text enlarged through the root and body font size, injected
  before each page's own scripts (WCAG 1.4.4 checks). Text set in px on an
  element is left as the site set it, as a browser's text-size setting does.
- `network`: latency and failure on the task's submission route; applied by
  the loop when it answers the endpoint.
"""

from contextlib import contextmanager
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # Playwright is needed only when a run starts
    from playwright.sync_api import Page

# A few Playwright device descriptors, copied so a config can be validated
# without starting Playwright. Values from Playwright's deviceDescriptors.
DEVICES = {
    "iPhone 13": {
        "viewport": {"width": 390, "height": 664},
        "screen": {"width": 390, "height": 844},
        "device_scale_factor": 3,
        "is_mobile": True,
        "has_touch": True,
        "user_agent": (
            "Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15 "
            "(KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1"
        ),
    },
    "Pixel 7": {
        "viewport": {"width": 412, "height": 839},
        "screen": {"width": 412, "height": 915},
        "device_scale_factor": 2.625,
        "is_mobile": True,
        "has_touch": True,
        "user_agent": (
            "Mozilla/5.0 (Linux; Android 14; Pixel 7) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/131.0.0.0 Mobile Safari/537.36"
        ),
    },
}


def needs_own_context(env) -> bool:
    return env.device is not None or env.viewport is not None or env.text_scale != 1.0


@contextmanager
def environment_page(page: "Page", env):
    """The page a run uses. With the default environment that is `page`
    itself; otherwise a new page in a new context of the same browser, set up
    for `env` and closed afterwards."""
    if not needs_own_context(env):
        yield page
        return
    options: dict = dict(DEVICES[env.device]) if env.device else {}
    if env.viewport is not None:
        options["viewport"] = {"width": env.viewport.width, "height": env.viewport.height}
        options.pop("screen", None)
    context = page.context.browser.new_context(**options)
    try:
        own = context.new_page()
        if env.text_scale != 1.0:
            own.add_init_script(script=_text_scale_script(env.text_scale))
        yield own
    finally:
        context.close()


def _text_scale_script(scale: float) -> str:
    css = (
        f"html{{font-size:{100 * scale:g}% !important}}"
        f"body{{font-size:{16 * scale:g}px !important}}"
    )
    return (
        "document.addEventListener('DOMContentLoaded', () => {"
        "const s = document.createElement('style');"
        "s.dataset.simux = 'text-scale';"
        f"s.textContent = {css!r};"
        "document.head.appendChild(s); });"
    )
