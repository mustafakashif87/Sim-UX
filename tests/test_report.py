"""agent/report.py: findings as change requests."""

from agent.report import element_for, fixes
from grounding.ground import default_signal_map


def test_every_signal_has_a_problem_and_a_fix():
    missing = [s for s in default_signal_map().signals() if not fixes().get(s, {}).get("fix")]
    assert missing == []
    assert all(entry.get("problem") for entry in fixes().values())


def test_element_for_reads_role_and_name_of_a_ref():
    tree = (
        '- main [ref=e4]:\n  - heading "Create account" [level=1] [ref=e5]\n'
        '  - textbox "Email" [ref=e7]'
    )
    assert element_for(tree, "e5") == 'heading "Create account"'
    assert element_for(tree, "e4") == "main"
    assert element_for(tree, "e9") is None
