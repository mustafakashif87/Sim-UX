"""The comparison table from synthetic results: no browser, no model."""

import json

from agent.compare import build, markdown, single_prompt_signals


def test_detection_needs_a_buggy_only_difference():
    axe = {"promo-a.html": {"image-alt", "region"}, "promo-b.html": {"region"}}
    sweep = {"basket-a.html": {"keyboard_trap"}}
    single = {
        "signup-a.html": {"data_loss_on_error"},
        "signup-b.html": set(),
        "order-a.html": {"duplicate_submission"},
        "order-b.html": {"duplicate_submission"},  # same on clean: not detected
    }
    rows = {r.bug.id: r for r in build([], axe, sweep, single)}
    assert rows["SB-01"].detected["axe"] and rows["SB-01"].cells["axe"] == "yes: image-alt"
    assert rows["SB-04"].detected["keyboard_sweep"]
    assert rows["B1"].detected["single_prompt"]
    assert not rows["B4"].detected["single_prompt"]
    assert rows["B1"].cells["simux"] == "not run"
    assert "| **Detected** |" in markdown(list(rows.values()))


def test_single_prompt_keeps_known_signals_only():
    reply = {"problems": [{"signal": "redundant_entry"}, {"signal": "made_up"}, "junk"]}
    assert single_prompt_signals(lambda m: json.dumps(reply), "task", "tree") == {"redundant_entry"}
    assert single_prompt_signals(lambda m: "not json", "task", "tree") == set()
