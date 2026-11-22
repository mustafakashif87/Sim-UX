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
| B1 | `signup-a.html` | `signup-b.html` | P1 Error-prone | `data_loss_on_error` | #9 | 3.3.7 Redundant Entry | A validation error clears every field (`form.reset()`), including the valid name |
| B2 | `subscribe-a.html` | `subscribe-b.html` | P1 Error-prone | `error_not_identified` | #9 | 3.3.1 Error Identification | An invalid email is rejected silently: no alert, no `aria-invalid`, nothing sent |
| B3 | `callback-a.html` | `callback-b.html` | P1 Error-prone | `error_not_actionable` | #9 | 3.3.3 Error Suggestion | Every error says only "Invalid input." (the alert and `aria-invalid` are still there); it never names the field or the fix |
| B4 | `order-a.html` | `order-b.html` | P1 Error-prone | `duplicate_submission` | #5 | 3.3.4 Error Prevention | "Place order" is not disabled after the first press, so a double press sends two orders |
| B5 | `account-a.html` | `account-b.html` | P1 Error-prone | `destructive_without_confirm` | #5, #3 | 3.3.4 Error Prevention | "Delete account" deletes at once; the clean page asks in a dialog first |
| B6 | `checkout-a.html` | `checkout-b.html` | P1 Error-prone | `redundant_entry` | #6 | 3.3.7 Redundant Entry | Step 3 asks for the billing address with empty fields; the clean page pre-fills it from step 1 |
| B7 | `returns-a.html` | `returns-b.html` | P2 Memoryless | `recall_required` | #6 | 3.3.2 Labels or Instructions | The return reference shown on step 1 must be typed on step 3, which does not show it again; the clean page repeats it beside the field |
| B8 | `renew-a.html` | `renew-b.html` | P2 Memoryless | `lost_location` | #1 | 2.4.2 Page Titled | All three steps of the wizard keep one `<title>` ("SimShop Plus – SimShop"); the clean page names the step in the title |
| B9 | `upgrade-a.html` | `upgrade-b.html` | P2 Memoryless | `no_progress_indicator` | #1 | 2.4.6 Headings and Labels | Every step of the wizard has the heading "Change your plan" and no "Step N of 3"; the clean page's headings name each step and its number |
| B10 | `transfer-a.html` | `transfer-b.html` | P3 Low-literacy | `label_unintelligible` | #2 | 3.3.2 Labels or Instructions | The submit button reads "Effectuate remittance"; the clean page says "Send money" |
| B11 | `cancel-a.html` | `cancel-b.html` | P3 Low-literacy | `instruction_unintelligible` | #2 | 3.1.5 Reading Level (AAA, advisory) | The instruction naming the word to type (STOP) is written in legal jargon; the clean page says it plainly |
| B12 | `phone-a.html` | `phone-b.html` | P3 Low-literacy | `system_language` | #2 | none (Nielsen only) | A number with a space is rejected with "ERR_VALIDATION_422"; the clean page says what to type |
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
| B1 to B12 | Per task in [`tasks.yaml`](tasks.yaml), with the task text and endpoint |
| SB-01 to SB-05 | `heading`, "Submission received" (on `success.html`) |

B1 to B12 pages send their submission as a `POST` to a relative `api/...` URL,
which the harness answers (`Task.endpoint`). **Serve the pages over HTTP**
(GitHub Pages, or `python -m http.server -d test-app`), never as `file://`: from
`file://` the relative POST fails, the goal never appears and every run ends in
give-up. Checked with the real loop and the fake model: over HTTP, correct runs
succeed on every page with no findings.

**B6 uses `redundant_entry`** (decided 22 Nov 2026): a value the persona
typed on an earlier step is typed again into an empty field with a different
name later in the same flow (WCAG 3.3.7). It is deterministic and reads the
intended `type` actions, so a typo does not hide the repeat.

## What each bug looks like to the harness

- **B1** shows across two observations: a field has a value before the submit
  and is empty after it, while an alert is showing.
- **B2** shows as "Nothing visibly changed." after a submit, with no POST.
- **B3** has an alert with text, but the text names no field.
- **B4** shows in the network log: two identical POSTs to `api/orders` in one
  step (from the double-submit perturbation).
  Every other B1 to B12 page disables its final button once the submission
  passes validation, in both versions, so P1's double press sends one POST
  there. Otherwise a double press anywhere would be a `duplicate_submission`
  finding this file does not list. `check_seeds.py` checks it with the
  submissions held unanswered, as a slow server would.
- **B5** shows as a POST to `api/account/delete` in the step that pressed
  "Delete account", with no dialog in between.
- **B6** shows on step 3 as empty "Billing street address" and "Billing city"
  fields for values the task already gave on step 1.
- **B7** shows across the step history: "RTN-48213" is in the step 1
  observation but not in the step 3 one, where a "Return reference" field
  needs it. With no memory (P2) the persona cannot know it; the baseline,
  with full memory, can.
- **B8** is not in the accessibility tree at all: only `document.title`
  stays the same across the steps. The harness logs the page title with each
  observation (not shown to the persona), and `lost_location` reads it.
- **B9** shows in the tree: the step heading is "Change your plan" on all
  three steps and no text says "Step N of 3".
- **B10** to **B12** show only through P3's vocabulary filter: the button
  name (B10) and the instruction (B11) become mostly `[unknown]`, and the
  error text (B12) is an internal code. The words a user needs on each clean
  page are common ones, so the clean page survives the filter.
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
