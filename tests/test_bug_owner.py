"""Which persona each seeded bug is evaluated under (agent.evaluate.bugs_for)."""

from agent.evaluate import bugs_for, persona_numbers
from agent.persona import PERSONAS_DIR
from agent.tasks import load_seeded_bugs


def test_every_persona_file_has_its_number():
    numbers = persona_numbers()
    assert sorted(numbers.values()) == sorted(p.stem for p in PERSONAS_DIR.glob("*.yaml"))
    assert numbers["P1"] == "error_prone"
    assert numbers["P14"] == "older_adult"


def test_b36_belongs_to_p14_not_p9():
    # B36's signal (data_lost_on_timeout) comes from P9's detectors and is
    # shared with P14 through `also:`; SEEDED_BUGS.md names P14.
    assert [b.id for b in bugs_for("older_adult")] == ["B36"]
    assert [b.id for b in bugs_for("interrupted")] == ["B26", "B27"]


def test_every_persona_bug_runs_under_the_persona_it_names():
    numbers = persona_numbers()
    owned = {pid: {b.id for b in bugs_for(pid)} for pid in numbers.values()}
    for bug in load_seeded_bugs():
        named = numbers.get(bug.detected_by.split(" ", 1)[0])
        if named and bug.signal:
            assert bug.id in owned[named], f"{bug.id} not run under {named}"
            assert sum(bug.id in ids for ids in owned.values()) == 1, bug.id
