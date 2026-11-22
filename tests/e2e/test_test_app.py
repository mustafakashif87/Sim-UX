"""P1 and its detectors on the real seeded test app (test-app/), served over HTTP.

Which page is buggy comes from SEEDED_BUGS.md and each task from tasks.yaml,
so this test follows the test-app author's ground truth rather than copying
it. If a page changes so that a detector no longer fires on its buggy page,
or fires on its clean one, this fails.
"""

import tempfile
from pathlib import Path

import pytest

from agent.contracts import Action
from agent.detectors import detect, load_run
from agent.fake_model import FakeModel, click, find_ref, press, type_into
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


def forced(pid, perturbation=None, network=None):
    """A persona with its mistake made certain, so the fixture test is
    deterministic; the evaluation uses the configured rates."""
    data = load_persona(pid).model_dump()
    if perturbation is not None:
        data["perturbation"] = {"seed": 1, **perturbation}
    if network is not None:
        data["environment"]["network"] = network
    return Persona.model_validate(data)


def with_env(pid, perturbation=None, **environment):
    """A persona with its environment (interruptions, clock) set for a test."""
    data = load_persona(pid).model_dump()
    data["environment"] |= environment
    if perturbation is not None:
        data["perturbation"] = {"seed": 1, **perturbation}
    return Persona.model_validate(data)


def click_any(*names):
    """Click the first button with any of these names (a save button renamed
    from screen to screen)."""

    def step(obs):
        for name in names:
            ref = find_ref(obs.tree, "button", name)
            if ref:
                return Action(thought=f"click {name}", action="click", ref=ref)
        return Action(thought="no save button", action="give_up")

    return step


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
    "B2": (  # a mistyped email: no @
        p1(),
        [type_into("Email address", "sam.khan.example.com"), click("Subscribe")],
    ),
    "B3": (  # a phone number one digit short
        p1(),
        [
            type_into("Your name", "Sam Khan"),
            type_into("Phone number", "0300123456"),
            click("Request callback"),
        ],
    ),
    "B4": (p1(double_submit_rate=1.0), [click("Place order")]),  # a double press
    "B5": (p1(), [click("Delete account"), click("Yes, delete my account")]),
    "B6": (  # the persona types what each step asks for, as the task gives it
        p1(),
        [
            type_into("Full name", "Sam Khan"),
            type_into("Street address", "12 Canal Road"),
            type_into("City", "Lahore"),
            click("Continue"),
            click("Continue"),
            type_into("Billing street address", "12 Canal Road"),
            type_into("Billing city", "Lahore"),
            click("Place order"),
        ],
    ),
    # P2 Memoryless: the script stops where a user without memory is stuck.
    "B7": (
        load_persona("memoryless"),
        [
            click("Stainless steel kettle", role="radio"),
            click("Continue"),
            click("It arrived damaged", role="radio"),
            click("Continue"),
        ],
    ),
    "B8": (  # stuck on step 1 three times, then on to step 2
        load_persona("memoryless"),
        [
            click("Continue"),
            click("Continue"),
            click("Continue"),
            click("Monthly, $4 a month", role="radio"),
            click("Continue"),
        ],
    ),
    "B9": (
        load_persona("memoryless"),
        [
            click("Family, $7 a month for up to five people", role="radio"),
            click("Continue"),
            click("Every month", role="radio"),
            click("Continue"),
            click("Confirm change"),
        ],
    ),
    # P3 Low-literacy: names as the vocabulary filter leaves them.
    "B10": (
        load_persona("low_literacy"),
        [
            type_into("Account number", "12345678"),
            type_into("Amount in rupees", "500"),
            click("Send money"),  # not on the buggy page: the persona is stuck
        ],
    ),
    "B11": (
        load_persona("low_literacy"),
        [type_into("Confirmation", "STOP"), click("Submit")],
    ),
    "B12": (
        load_persona("low_literacy"),
        [type_into("Phone number", "0300 1234567"), click("Save")],
    ),
    # P4 Screen-reader (B13 to B15)
    "B13": (
        load_persona("screen_reader"),
        [type_into("Your feedback", "Fast delivery, thank you"), click("Send feedback")],
    ),
    "B14": (
        load_persona("screen_reader"),
        [click("UK 8", role="radio"), click("Add to basket")],
    ),
    "B15": (load_persona("screen_reader"), [click("Accept the policy", role="link")]),
    # P5 Keyboard-only (B16, B17): Tab, then type where focus is
    "B16": (
        load_persona("keyboard_only"),
        [
            press("Tab"),
            type_into("Lowest price", "20"),
            press("Tab"),
            press("Tab"),
            type_into("Highest price", "50"),
            press("Tab"),
            press("Enter"),
        ],
    ),
    "B17": (
        load_persona("keyboard_only"),
        [
            press("Tab"),
            press("Tab"),
            type_into("Email address", "sam.khan@example.com"),
            press("Tab"),
            type_into("Password", "Kettle-2026"),
            press("Tab"),
            press("Enter"),
        ],
    ),
    # P7 Low-vision (B20 to B22)
    "B20": (load_persona("low_vision_zoom"), [click("Pay invoice")]),
    "B21": (load_persona("low_vision_zoom"), [press("Tab"), press("Tab"), press("Tab")]),
    "B22": (load_persona("low_vision_zoom"), []),
    # P8 Skimmer (B23 to B25)
    "B23": (
        load_persona("skimmer"),
        [type_into("Gift card code", "RCPT-5520"), click("Redeem")],
    ),
    "B24": (load_persona("skimmer"), [click("Start free trial")]),
    "B25": (load_persona("skimmer"), [click("Choose Family, $7 a month")]),
    # P6 Mobile touch (B18, B19): every tap is imprecise here
    "B18": (
        forced("touch_imprecise", {"mis_tap_base_rate": 1.0, "mis_tap_cap": 1.0}),
        [click("Increase quantity"), click("Go to checkout")],
    ),
    "B19": (
        forced("touch_imprecise", {"mis_tap_base_rate": 1.0, "mis_tap_cap": 1.0}),
        [click("Standard (free)", role="radio"), click("Pay now")],
    ),
    # P10 Slow connection (B28, B29)
    "B28": (
        forced("slow_network", {"impatient_retry_rate": 1.0}, {"latency_ms": 3000}),
        [click("Pay now")],
    ),
    "B29": (
        forced("slow_network", {}, {"fail_rate": 1.0}),
        [type_into("Meter reading", "48213"), click("Send reading")],
    ),
    # P9 Interrupted (B26, B27)
    "B26": (
        with_env("interrupted", interruptions=[{"at_step": 2, "kind": "idle", "seconds": 900}]),
        [
            type_into("Full name", "Sam Khan"),
            type_into("National ID number", "35202-1234567-1"),
            click("Sign in again"),
            click("Submit application"),
        ],
    ),
    "B27": (
        with_env("interrupted", interruptions=[{"at_step": 2, "kind": "reload"}]),
        [
            click("Every week", role="radio"),
            click("Next"),
            click("Card", role="radio"),
            click("Next"),
        ],
    ),
    # P11 Help-seeker (B30, B31)
    "B30": (
        load_persona("help_seeker"),
        [
            type_into("Policy number", "1234567"),
            type_into("What happened", "My phone screen broke"),
            click("Make a claim"),
            click("Make a claim"),
            click("Make a claim"),
            click("Where do I find my policy number?", role="link"),
        ],
    ),
    "B31": (
        load_persona("help_seeker"),
        [
            type_into("Tracking number", "SP-48213"),
            click("Next"),
            click("Saturday", role="radio"),
            click("Next"),
            click("Confirm change"),
        ],
    ),
    # P12 Habitual (B32, B33): every possible capture happens here
    "B32": (
        forced("habitual", {"capture_rate": 1.0}),
        [
            click("Send me email receipts", role="checkbox"),
            click_any("Save", "Apply", "Update"),
            click("Hide my reviews from other shoppers", role="checkbox"),
            click_any("Save", "Apply", "Update"),
            click("Tell me about offers by email", role="checkbox"),
            click_any("Save", "Apply", "Update"),
        ],
    ),
    "B33": (
        load_persona("habitual"),
        [click("Toasters", role="link"), click("Basket", role="link"), click("Check out")],
    ),
    # P13 Power user (B34, B35)
    "B34": (
        load_persona("power_user"),
        [type_into("Item name", "Kettle"), type_into("Quantity", "3"), press("Enter")],
    ),
    "B35": (
        load_persona("power_user"),
        [click("Select all", role="checkbox"), click("Archive selected"), click("Yes, archive")],
    ),
    # P14 Older adult (B36): slow and, here, always imprecise
    "B36": (
        forced(
            "older_adult",
            {"mis_tap_base_rate": 1.0, "mis_tap_cap": 1.0, "mis_tap_reach_px": 8},
        ),
        [
            type_into("Full name", "Sam Khan"),
            type_into("Phone number", "03001234567"),
            click("Yes, more time"),
            type_into("Preferred date", "2 December"),
            click("Book appointment"),
        ],
    ),
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
