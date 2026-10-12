# Seeded bugs: ground truth for the test app

The single ground-truth file for `test-app/`. Recall, precision and the
false-positive rate (spec: Evaluation protocol) are scored against this table.
Each bug has a **buggy** page (`-a`) and a **clean** page (`-b`) that differ
only in that bug. The clean page is the "Persona on clean" condition.

Page names, text, IDs and anything that reaches the accessibility tree are
neutral. The bug is named here and nowhere else, so the agent gets no hints.
`check_seeds.py` parses the table below. Every row needs a matching check
there, or CI fails.

## Bugs

| ID | Buggy page | Clean page | Detected by | Expected signal | Nielsen | WCAG 2.2 | Bug |
| --- | --- | --- | --- | --- | --- | --- | --- |
| SB-01 | `promo-a.html` | `promo-b.html` | axe-core | `image-alt` | n/a | 1.1.1 Non-text Content | Promo image has no `alt`; its offer text ("20% off… WELCOME20") appears nowhere else |
| SB-02 | `search-a.html` | `search-b.html` | axe-core | `button-name` | n/a | 4.1.2 Name, Role, Value | Icon-only submit button with no accessible name |
| SB-03 | `contact-a.html` | `contact-b.html` | axe-core | `label` | n/a | 1.3.1 Info and Relationships | Email field's visible text is not a `<label>`, so the field has no name |
| SB-04 | `basket-a.html` | `basket-b.html` | keyboard sweep | Tab-cycle trap | n/a | 2.1.2 No Keyboard Trap | Script cycles Tab/Shift+Tab inside the promo-code box; "Place order" is never reached |
| SB-05 | `booking-a.html` | `booking-b.html` | keyboard sweep | unreachable control | n/a | 2.1.1 Keyboard | "Confirm booking" is a `<div>` with a click handler only: not focusable, no role |

## Goal checks

The harness decides success: a run succeeds when a visible element with this
role and name appears (`agent.loop.Goal`).

| Pages | Goal (role, name) |
| --- | --- |
| SB-01 to SB-05 | `heading`, "Submission received" (on `success.html`) |

## What each bug looks like to the harness

- **SB-01/02/03** appear in `aria_snapshot()` as `img`, `button` and `textbox`
  nodes **with no name**. Pruned snapshots drop unnamed nodes, so read the tree
  with `locator.aria_snapshot()`.
- **SB-04** is invisible in any single snapshot. It shows only in the step
  history: focus repeats between the same two elements.
- **SB-05** appears as `text: Confirm booking` where the clean page has
  `button "Confirm booking"`.

SB-01 to SB-05 are the proposal-era keyboard and accessibility bugs. Since the
persona change (spec: Purpose) they are fixtures for the deterministic layer:
axe-core for SB-01 to SB-03, the keyboard sweep for SB-04 and SB-05.

`index.html` (neutral links to every page) and `success.html` are not test
targets.
