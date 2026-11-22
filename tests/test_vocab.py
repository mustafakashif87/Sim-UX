"""P3's vocabulary filter (spec, P3: the word list and UI allowlist)."""

import pytest

from agent.perception import apply_filters, parse_snapshot, render
from agent.vocab import common_words, known, simplify, ui_allowlist, unknown_share


def test_lists_load():
    assert len(common_words()) == 2809  # NGSL 1.2 headwords
    assert 30 <= len(ui_allowlist()) <= 50  # spec: about 30 to 50 words


@pytest.mark.parametrize(
    "word",
    ["send", "sends", "sent", "money", "ordered", "stopping", "cities", "easily", "Email",
     "password", "SimShop", "Monday", "two", "rupees", "confirmation"],
)  # fmt: skip
def test_known(word):
    assert known(word)


@pytest.mark.parametrize(
    "word",
    ["effectuate", "remittance", "notwithstanding", "hereinbefore", "forthwith", "inscription"],
)
def test_seeded_jargon_is_unknown(word):
    assert not known(word)


@pytest.mark.parametrize(
    "clean",
    [
        "Send money",
        "Amount in rupees",
        "Account number",
        "To end your membership, type the word STOP in the box below.",
        "Enter the number as 11 digits with no spaces, like 03001234567.",
        "Phone number",
        "Save",
        "Cancel",
    ],
)
def test_clean_page_words_survive(clean):
    assert simplify(clean) == clean


def test_names_numbers_and_addresses_are_kept():
    assert simplify("Deliver to Sam Khan, 12 Canal Road, Lahore") == (
        "Deliver to Sam Khan, 12 Canal Road, Lahore"
    )
    assert simplify("Write to sam.khan@example.com") == "Write to sam.khan@example.com"


def test_jargon_button_is_unknown():
    assert simplify("Effectuate remittance") == "[unknown] [unknown]"
    assert unknown_share("[unknown] [unknown]") == 1.0


def test_content_share_ignores_function_words():
    text = simplify("Termination shall be effectuated forthwith upon the inscription of STOP.")
    assert unknown_share(text) < unknown_share(text, content_only=True)


def test_filter_keeps_typed_values_and_refs():
    tree = """- button "Effectuate remittance" [ref=e3]
- textbox "Account number" [ref=e2]: notwithstanding
- paragraph [ref=e4]: Remittance forthwith"""
    out = render(apply_filters(parse_snapshot(tree), ["vocab_filter"]))
    assert 'button "[unknown] [unknown]" [ref=e3]' in out
    assert 'textbox "Account number" [ref=e2]: notwithstanding' in out  # typed value
    assert "[unknown] [unknown]" in out.splitlines()[-1]
