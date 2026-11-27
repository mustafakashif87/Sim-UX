"""P5 keyboard-only detectors on hand-built run logs (no browser).

B16 (filters-a.html): positive tabindex sends focus from "Lowest price" (the
first Tab stop) to the footer link and up to "Highest price"; a confused run
that bounces back to "Lowest price" instead used to read as a keyboard trap
only, because every return to the first Tab stop was excused as a wrap.
"""

from agent.contracts import Action, FocusedElement, Observation, StepRecord
from agent.detectors import RunLog
from agent.detectors.extension import focus_order_illogical, keyboard_trap_in_task

TAB = Action(thought="", action="press", key="Tab")
BOXES = {"e1": [50, 100], "e2": [50, 800], "e3": [50, 150], "e4": [50, 200]}


def focused(ref):
    return FocusedElement(ref=ref, role="textbox", name=ref) if ref else None


def run_log(refs):
    """refs[i] is what Tab press i focuses; refs[0] follows the first press."""
    observations = [Observation(step=0, tree="", url_path="/filters-a.html", focused=None)]
    steps = []
    facts = [{"boxes": BOXES, "scroll_y": 0}]
    for i, ref in enumerate(refs):
        observations.append(
            Observation(step=i + 1, tree="", url_path="/filters-a.html", focused=focused(ref))
        )
        facts.append({"boxes": BOXES, "scroll_y": 0})
        steps.append(
            StepRecord(
                run_id="r1",
                persona="keyboard_only",
                page="filters-a.html",
                step=i,
                observation_hash="h",
                intended_action=TAB,
                executed_action=TAB,
                result="ok",
                goal_reached=False,
            )
        )
    meta = {
        "run_id": "r1",
        "persona": "keyboard_only",
        "page": "filters-a.html",
        "status": "max_steps",
    }
    return RunLog(meta, steps, observations, [], facts=facts)


def test_forward_tab_order_flags_the_upward_jumps():
    # min(e1) -> footer(e2, down, fine) -> max(e3, UP) -> submit(e4, down) -> wraps to min
    run = run_log(["e1", "e2", "e3", "e4", "e1", "e2", "e3", "e4"])
    finding = focus_order_illogical(run)
    assert finding.evidence_steps == [2, 6]
    assert keyboard_trap_in_task(run) is None


def test_single_end_of_page_wrap_is_not_a_violation():
    run = run_log(["e1", "e2", "e3", "e4", "e1"])
    assert focus_order_illogical(run).evidence_steps == [2]


def test_repeated_return_to_the_first_stop_is_not_excused_as_a_wrap():
    # confused persona bounces between the first Tab stop and the footer
    # link without ever reaching "max": every return to e1 used to be
    # treated as the legitimate wrap and dropped, so only the trap detector
    # fired. B16's bug is focus order, so it must be found too.
    run = run_log(["e1", "e2", "e1", "e2", "e1", "e2"])
    assert focus_order_illogical(run) is not None
    assert keyboard_trap_in_task(run) is not None
