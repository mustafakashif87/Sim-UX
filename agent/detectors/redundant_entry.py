"""`redundant_entry` (B6): the flow asks again for something already given.

WCAG 3.3.7 Redundant Entry, Nielsen #6. Not in the spec's first P1 table;
added to close the open B6 note in test-app/SEEDED_BUGS.md.

A step counts when the persona typed a value into an empty field and had
already typed the same value (ignoring case and surrounding spaces) into a
field with a different name earlier in the run. Values come from what the
model intended, so a typo in either entry does not hide the repeat. Values
shorter than MIN_LENGTH (a "1", a "y") are too common to count.

A page that pre-fills the second field leaves it non-empty, so typing over
it is the persona's choice, not the page's demand.
"""

from agent.contracts import Finding
from agent.detectors import RunLog, make_finding
from agent.detectors._tree import by_ref

SIGNAL = "redundant_entry"
MIN_LENGTH = 3


def redundant_entry(run: RunLog) -> Finding | None:
    typed: dict[str, set[str]] = {}  # value -> names of the fields it went into
    evidence = []
    for step in run.steps:
        intended = step.intended_action
        if intended.action != "type" or step.result != "ok" or not intended.text:
            continue
        field = by_ref(run.observations[step.step], intended.ref)
        if field is None:
            continue
        value = intended.text.strip().casefold()
        name = field.name or ""
        earlier = typed.setdefault(value, set())
        was_empty = not (field.text or "").strip()
        if len(value) >= MIN_LENGTH and was_empty and earlier - {name}:
            evidence.append(step.step)
        earlier.add(name)
    return make_finding(run, SIGNAL, evidence) if evidence else None
