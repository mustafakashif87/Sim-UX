# SimUX Persona Catalogue: P4 to P14

As of 2026-11-15. Draft for team review. Extends `persona-design-spec.md`, which stays the source of truth for P1 to P3, the evaluation protocol and the grounding pipeline.

## Why more personas

The spec's three personas each change one constraint axis, and between them they cover 6 of Nielsen's 10 heuristics and no WCAG criteria under Perceivable or Robust. The spec explains the gap by saying #7, #8 and #10 "are judgements no hard constraint can model without roleplay". This catalogue disputes that. Each persona below models those heuristics through a limit the harness enforces: a step budget tied to the shortest path (#7), a filter on what the user reads (#8), and a rule that limits the user to help-seeking actions once they are stuck (#10).

With P1 to P14 together:

- **All 10 Nielsen heuristics** have at least one observed-failure signal (currently 6).
- **All 4 WCAG principles** have at least one behavioural signal (currently 1). Four of those criteria are new in WCAG 2.2: 2.4.11, 2.5.8, 3.2.6 and 3.3.7.
- Every persona still passes the spec's rule: **delete the system prompt and the persona's limits still hold.**

## The rule, restated for new personas

A persona is acceptable only if:

1. Every limit is enforced in exactly one harness module and is logged.
2. Its realism basis is a published study of real users, not a stereotype.
3. Each signal is deterministic where possible, and model-judged signals are labelled as such.
4. Every seeded bug has a buggy and a clean page that differ only in that bug, and the unconstrained baseline succeeds on the buggy page. If the baseline fails, the page is inconclusive, as in the spec.

## Use cases: who would run which persona

SimUX is pitched as a product, so each persona must answer one question: who would run this, and before what?

| Team | Situation | Personas they run | What they get |
| --- | --- | --- | --- |
| Public sector or regulated service (government, banking, health) | Accessibility compliance before launch: European Accessibility Act (in force since June 2025), UK public sector regulations, ADA cases | P4 Screen-reader, P5 Keyboard-only, P7 Low-vision, P11 Help-seeker | Not only a list of violations (axe already gives that) but **which violations block a real task**, ranked by severity |
| E-commerce, mobile-first | Conversion drop on mobile checkout | P6 Touch, P8 Skimmer, P10 Slow-connection, P1 Error-prone | Mis-taps, buried calls to action and missing loading feedback, each with step-by-step evidence |
| Insurance, tax and benefits forms | Long forms that users abandon partway through | P9 Interrupted, P2 Memoryless, P14 Older adult, P11 Help-seeker | Timeouts, data lost on return, steps that rely on recall |
| SaaS products | Redesigns that break returning users | P12 Habitual, P13 Power user | Inconsistent labels and layout between pages, and needless extra steps |
| Any team, in CI | A regression gate on every pull request | A "persona pack" (see below) | A failed check when a change brings back a known class of bug |

**Persona packs** (a product feature for the New Run screen): ready-made bundles so users don't need to know the persona list.

| Pack | Personas |
| --- | --- |
| Accessibility | P4, P5, P7 |
| Mobile | P6, P8, P10 |
| Forms and errors | P1, P2, P9, P11 |
| Returning users | P12, P13 |
| Inclusive (everything) | P1 to P14 |

## Framework changes needed

The spec has four axes. P4 to P14 need a **fifth axis, Environment**: what the world does to the user, separate from what the user does wrong. It is enforced in `browser.py`, so it stays inside the one-module-per-axis rule.

| Axis | New settings | Enforced in | Used by | Size |
| --- | --- | --- | --- | --- |
| Perception | `viewport_only`, `skim_text`, `linear_window`, `visible_focus_only` | `perception.py` (needs bounding boxes and focus styles from Playwright, harness-side only) | P4, P5, P7, P8, P14 | M |
| Action space | Clicks allowed only on interactive roles; `escalation` (help-only mode once stuck) | `actions.py` validator | P4, P11 | S |
| Memory and budget | `prior_knowledge` (a learned map from an earlier run); `budget: optimal_x` (step cap as a multiple of the shortest path) | `loop.py`, plus `optimal_steps` in `tasks.yaml` | P12, P13 | M |
| Perturbation | `mis_tap` (depends on target size), `impatient_retry`, `capture` (habit slip) | `perturb.py` | P6, P10, P12, P14 | M |
| **Environment (new)** | `device` (Playwright device descriptor), `viewport`, `text_scale`, `network` (latency, failure), `think_time_s` and `interruptions` (Playwright `page.clock`) | `browser.py`, `loop.py` | P6, P7, P9, P10, P14 | M |

`persona.py` validates configs strictly, so each new key below is a **proposed schema**. It needs adding to the Pydantic models, with a "not built yet" stub like the one `vocab_filter` uses now.

**Simulated time.** Personas that wait (P9, P14) use Playwright's clock API (`page.clock.fast_forward`), not real sleeps. A 2-minute timeout costs milliseconds of CI time, and runs stay deterministic.

---

## P4 Screen-reader user

**Config ID:** `screen_reader` · **Axis:** Perception and action space

**Who it stands for:** blind and severely visually impaired people who use a screen reader (NVDA, JAWS, VoiceOver). They hear a page one item at a time in reading order, and they move around it by headings and landmarks.

**Use case:** a compliance team wants to know which axe-core violations stop a blind user from finishing checkout, not just how many there are. This persona turns static violations into task-blocking findings with severity.

**Constraint:**

- `linear_window`: the model sees only about 15 nodes around its reading position, not the whole tree. `scroll` reads further on. The harness also lists the page's headings and landmarks, as a screen reader's rotor menu does. A page with no headings therefore has to be read item by item, which uses up the step budget.
- Actions: `click` is accepted only on refs with an interactive role (`button`, `link`, `textbox`, `checkbox`, and so on). A `div` with a click handler is not exposed to a screen reader, so the persona cannot use it.
- Change announcements: after an action, new text reaches the persona only if it sits in a live region (`role=status`, `role=alert`, `aria-live`) or at the reading position. Other changes go unseen until the persona reads that far.

```yaml
id: screen_reader
perception:
  filters: [linear_window]
  window_nodes: 15            # proposed key
  rotor: [headings, landmarks] # proposed key
actions:
  allowed: [click, type, press, scroll, back]
  keys: [Tab, Shift+Tab, Enter, Space, Escape, ArrowDown, ArrowUp]
  interactive_roles_only: true # proposed key
memory:
  history_turns: 3
  max_steps: 25
task_types: [complete_form, navigate_to_info]
```

**Realism basis:** the WebAIM Screen Reader User Survey (latest edition), where navigating by headings is consistently the most common way to find information; and how screen readers present content as a linear virtual buffer.

| Signal | Detector | Type | Nielsen | WCAG 2.2 |
| --- | --- | --- | --- | --- |
| `non_semantic_control` | The goal path needs an element with no interactive role; the persona's click is rejected and the baseline's succeeds | Deterministic | #4 | 4.1.2 Name, Role, Value; 2.1.1 Keyboard |
| `unnamed_control` | A goal-path control has an empty accessible name and the persona picks wrong or gives up | Deterministic | #6 | 4.1.2 Name, Role, Value |
| `status_not_announced` | After a submit, new text appears outside any live region and the persona repeats the action or gives up | Deterministic | #1 | 4.1.3 Status Messages |
| `no_structure` | The page has no headings or landmarks, the goal control is past position 40 in reading order, and the persona hits the step cap | Deterministic | #8 | 1.3.1 Info and Relationships; 2.4.1 Bypass Blocks |
| `image_only_info` | Task-critical information exists only in an image with no text alternative | Deterministic | #6 | 1.1.1 Non-text Content |

**Seeded bugs:**

| ID | Pages | Bug | Clean version |
| --- | --- | --- | --- |
| B13 | `feedback-a/b` | "Thanks, sent!" appears as plain red or green text with no live region | Message in `role=status` |
| B14 | `size-a/b` | Shoe-size picker is made of `div`s with click handlers | Radio group |
| B15 | `policy-a/b` | A long policy page with no headings or landmarks; the "Accept" link is at the bottom | Headings, a `main` landmark and a skip link |

It is also run on SB-01, SB-02, SB-03 and SB-05 to compare directly with axe-core and the keyboard sweep. **This is the headline result for the report:** axe-core finds all of these violations, and the persona shows which of them actually stop the task.

**Limits:** it models the reading model of a screen reader, not a particular product's quirks (NVDA and VoiceOver differ). Speech is not simulated.

---

## P5 Keyboard-only user

**Config ID:** `keyboard_only` · **Axis:** Action space and perception

**Who it stands for:** people with motor impairments who cannot use a mouse, switch and sip-and-puff users (whose devices act as keyboards), people with tremors, and power users. Sighted, so they rely on **seeing** where focus is.

**Use case:** finding focus traps, illogical tab order and invisible focus during a real task. The spec already plans this as "a one-line config change". This persona makes it a full member of the set rather than a footnote.

**Constraint:**

- Actions: `press` only. No click, no type-by-ref; text goes into whatever has focus.
- `visible_focus_only`: the observation's `focused` field is set to `null` when the focused element has **no visible focus indicator**. The harness compares the element's computed outline, border and box-shadow with and without focus. A sighted keyboard user on a page with `outline: none` doesn't know where they are, and neither does the persona.

```yaml
id: keyboard_only
perception:
  filters: [full_tree, visible_focus_only]
actions:
  allowed: [press, type]       # type goes to the focused element only (proposed rule)
  keys: [Tab, Shift+Tab, Enter, Space, Escape, ArrowDown, ArrowUp, ArrowLeft, ArrowRight]
memory:
  history_turns: 3
  max_steps: 30
task_types: [complete_form]
```

**Realism basis:** the WCAG 2.2 Understanding documents for 2.1.1, 2.4.3 and 2.4.7 (which describe these users), and WebAIM's keyboard accessibility guidance.

| Signal | Detector | Type | Nielsen | WCAG 2.2 |
| --- | --- | --- | --- | --- |
| `focus_not_visible` | The focused element on the goal path has no style change on focus, and the persona fails | Deterministic | #1 | 2.4.7 Focus Visible |
| `focus_order_illogical` | Tab order differs from visual reading order (inversions counted from bounding boxes) and the persona overshoots or loops | Deterministic | #4 | 2.4.3 Focus Order |
| `keyboard_trap` | Reuses the sweep's Tab-cycle detector, now during a task | Deterministic | #3 | 2.1.2 No Keyboard Trap |
| `keyboard_unreachable` | Reuses the sweep's unreachable-control detector | Deterministic | #7 | 2.1.1 Keyboard |

**Seeded bugs:**

| ID | Pages | Bug | Clean version |
| --- | --- | --- | --- |
| B16 | `filters-a/b` | Positive `tabindex` values send focus from "Price" to the footer, then back | DOM order matches visual order |
| B17 | `login-a/b` | `*:focus { outline: none }` with no replacement | Visible focus ring |

It is also run on SB-04 and SB-05, so the keyboard sweep and the persona can be compared.

---

## P6 Mobile touch user

**Config ID:** `touch_imprecise` · **Axis:** Environment and perturbation

**Who it stands for:** anyone on a phone (most web traffic), especially one-handed thumb use, people with large fingers, tremor or arthritis, and people on the move.

**Use case:** a shop whose mobile checkout converts worse than desktop. The persona shows the "Remove" icon that sits 4 px from the "+" button, and that a mis-tap there empties the basket with no undo.

**Constraint:**

- Environment: a Playwright mobile device (for example `iPhone 13`: 390×844 viewport, touch enabled, mobile user agent).
- Perturbation `mis_tap`: when the model clicks a target whose smaller side is `s` CSS px, the tap is redirected with probability `p = min(cap, base_rate × 44 / s)`. It lands on the nearest other interactive element within `reach_px` of the target's edge; if there is none, it lands on empty space (a miss). Intended and executed targets are both logged, as with every perturbation. The seeded RNG means runs replay exactly.

```yaml
id: touch_imprecise
environment:                   # proposed axis
  device: "iPhone 13"
perception:
  filters: [full_tree]
actions:
  allowed: [click, type, scroll, back]
memory:
  history_turns: 3
  max_steps: 20
perturbation:
  seed: 1234
  mis_tap_base_rate: 0.05      # at 44 px and above
  mis_tap_cap: 0.40
  mis_tap_reach_px: 12
task_types: [complete_form]
```

**Realism basis:** Fitts's law (Fitts, 1954); Parhi, Karlson and Bederson (2006), a target-size study for one-handed thumb use on small touchscreens; platform guidance (Apple's 44 pt, Material's 48 dp); and the WCAG 2.5.8 Understanding document.

| Signal | Detector | Type | Nielsen | WCAG 2.2 |
| --- | --- | --- | --- | --- |
| `target_too_small` | A goal-path target is under 24×24 CSS px without enough spacing (checked from bounding boxes), and a mis-tap occurred on it | Deterministic | #5 | 2.5.8 Target Size (Minimum) |
| `mis_tap_consequence` | A mis-tap triggered a state-changing request (POST) or selection, with no confirmation or undo | Deterministic | #5, #3 | 3.3.4 Error Prevention |
| `reflow_failure` | Shared with P7: the page needs horizontal scrolling at mobile width | Deterministic | #8 | 1.4.10 Reflow |

**Seeded bugs:**

| ID | Pages | Bug | Clean version |
| --- | --- | --- | --- |
| B18 | `cart-a/b` | A 16×16 px "Remove item" icon sits 4 px from the quantity "+", and removal is immediate | 44 px targets, spaced apart, with an undo toast |
| B19 | `shipping-a/b` | "Standard (free)" and "Express (£9.99)" radio buttons are 18 px tall and touching; there is no order summary before paying | Large tap rows and a summary showing the chosen option |

**Limits:** the mis-tap model is geometric. It does not model swipe gestures or drag, because the action set has no drag (and neither does the baseline, so drag-only bugs would be inconclusive).

---

## P7 Low-vision magnifier user

**Config ID:** `low_vision_zoom` · **Axis:** Environment and perception

**Who it stands for:** people with low vision who use 200% to 400% browser zoom or screen magnifiers, including many older users. At high magnification they see only a small part of the page at a time.

**Use case:** a council website that is fine at 100% but where, at 400% zoom, the "Pay" button is off-screen to the right and can only be reached by scrolling sideways. Few teams test at 400%.

**Constraint:**

- Environment: viewport of 320×256 CSS px, the WCAG 1.4.10 equivalent of 1280×1024 at 400%. `text_scale: 2.0` (text enlarged to 200% through a root font-size style) for the 1.4.4 checks.
- `viewport_only`: only nodes whose bounding box intersects the visible viewport reach the model. `scroll` is vertical only. A magnifier user can pan sideways, but pages that force it are the failure being tested, so horizontal content is out of reach. The baseline sees the full tree.

```yaml
id: low_vision_zoom
environment:
  viewport: {width: 320, height: 256}
  text_scale: 2.0
perception:
  filters: [viewport_only]
actions:
  allowed: [click, type, press, scroll, back]
  keys: [Tab, Enter, Escape]
memory:
  history_turns: 3
  max_steps: 25
task_types: [complete_form]
```

**Realism basis:** the WebAIM Survey of Users with Low Vision; the WCAG 2.2 Understanding documents for 1.4.4 and 1.4.10; WHO data on how common vision impairment is (check the current figure before citing).

| Signal | Detector | Type | Nielsen | WCAG 2.2 |
| --- | --- | --- | --- | --- |
| `reflow_failure` | `document.scrollWidth > viewport width`, and a goal-path control is horizontally out of view | Deterministic | #8 | 1.4.10 Reflow |
| `focus_obscured` | The focused element is fully covered by a sticky or fixed element (checked by bounding-box overlap) | Deterministic | #1 | 2.4.11 Focus Not Obscured (Minimum) |
| `text_clipped` | At 200% text, task-critical text is cut off (`scrollHeight > clientHeight` with `overflow: hidden`) | Deterministic | #8 | 1.4.4 Resize Text |

**Seeded bugs:**

| ID | Pages | Bug | Clean version |
| --- | --- | --- | --- |
| B20 | `invoice-a/b` | The form is in a fixed 1000 px wide layout; "Pay" is at the far right | Responsive single column |
| B21 | `profile-a/b` | A fixed cookie banner covers the bottom 70% of the viewport at 400% zoom, including the focused field | Banner that doesn't cover content, or can be closed |
| B22 | `notice-a/b` | The instruction box has a fixed height and `overflow: hidden`, so at 200% text the deadline is cut off | Height grows with content |

---

## P8 Skimmer (satisficer)

**Config ID:** `skimmer` · **Axis:** Perception and budget

**Who it stands for:** most web users, most of the time. People read in an F-shaped pattern, take in a small share of the words and pick the first option that looks good enough. This is ordinary behaviour, not a disability, which makes it important for conversion.

**Use case:** a marketing team whose landing page buries "Start free trial" below a hero banner and three promotions, or whose crucial instruction is in sentence four of a paragraph. This is the first SimUX persona that covers **Nielsen #8** (aesthetic and minimalist design) with an observed failure.

**Constraint:**

- `viewport_only` at 1280×720, so only what is above the fold until the persona scrolls.
- `skim_text`: every text node past `max_words` words is cut short with "…". Headings and control names are kept whole, because people scan these.
- A tight budget: 10 steps, 2 turns of history. Scrolling costs a step, which models the cost of scrolling.

```yaml
id: skimmer
environment:
  viewport: {width: 1280, height: 720}
perception:
  filters: [viewport_only, skim_text]
  skim_max_words: 8            # proposed key
actions:
  allowed: [click, type, press, scroll, back]
  keys: [Tab, Enter, Escape]
memory:
  history_turns: 2
  max_steps: 10
task_types: [complete_form, navigate_to_info]
```

**Realism basis:** Nielsen (2006), "F-shaped pattern for reading web content", from eye-tracking; Nielsen (2008), "How little do users read?"; Simon's satisficing (1956); Krug, *Don't Make Me Think*.

| Signal | Detector | Type | Nielsen | WCAG 2.2 |
| --- | --- | --- | --- | --- |
| `key_info_buried` | Text the task needs (listed as `critical_text` in `tasks.yaml`) starts past word N of its node; the persona fails and the baseline succeeds | Deterministic | #8 | 2.4.6 Headings and Labels |
| `cta_below_fold` | The goal-path control is outside the first viewport, and the persona runs out of budget or picks a decoy | Deterministic | #8 | none (Nielsen only) |
| `headings_not_descriptive` | Section headings on the goal path don't say what the section is for, so the persona opens the wrong one | Model-judged | #8, #2 | 2.4.6 Headings and Labels; 2.4.10 Section Headings (AAA) |

**Seeded bugs:**

| ID | Pages | Bug | Clean version |
| --- | --- | --- | --- |
| B23 | `redeem-a/b` | "Use the code from your email, not the one on your receipt" is the fourth sentence of a paragraph | The instruction is a short line next to the field |
| B24 | `trial-a/b` | "Start free trial" sits below a carousel and three promotional blocks | Call to action above the fold |
| B25 | `pricing-a/b` | Headings read "Section 1", "More info" and "Other" | "Monthly plans", "Annual plans", "Cancel anytime" |

---

## P9 Interrupted user

**Config ID:** `interrupted` · **Axis:** Environment and memory

**Who it stands for:** everyone who leaves a long form partway through: a parent filling in a benefits claim, a nurse on a break, a commuter whose train goes into a tunnel. Mobile sessions in particular come in short bursts.

**Use case:** government, insurance and visa forms where users come back after 20 minutes and find their session has expired and their answers are gone. This is one of the most-reported frustrations with public services.

**Constraint:**

- Environment `interruptions`: at set steps the harness injects an event:
  - `idle`: moves the page clock forward N seconds (Playwright clock, no real wait);
  - `reload`: reloads the page;
  - `tab_away`: hides the page (`visibilitychange`), then shows it again.
- Memory: after each interruption, the next step runs with `history_turns: 0`. The user comes back "cold" and has to work out where they were from what is on screen.

```yaml
id: interrupted
environment:
  interruptions:
    - {at_step: 2, kind: idle, seconds: 900}
    - {at_step: 3, kind: reload}
perception:
  filters: [full_tree]
actions:
  allowed: [click, type, press, scroll, back]
  keys: [Tab, Enter, Escape]
memory:
  history_turns: 3
  reset_after_interruption: true  # proposed key
  max_steps: 25
task_types: [multi_step_form]
```

**Realism basis:** Mark, Gudith and Klocke (2008), "The cost of interrupted work: more speed and stress", CHI; Altmann and Trafton (2002), "Memory for goals" (on resuming after an interruption); Oulasvirta et al. (2005), "Interaction in 4-second bursts", CHI.

| Signal | Detector | Type | Nielsen | WCAG 2.2 |
| --- | --- | --- | --- | --- |
| `timeout_no_warning` | The session ends during `idle` with no warning beforehand and no option to extend | Deterministic | #1, #3 | 2.2.1 Timing Adjustable |
| `data_lost_on_timeout` | Field values before `idle` are empty after logging back in | Deterministic | #9 | 2.2.5 Re-authenticating (AAA); 2.2.6 Timeouts (AAA) |
| `state_lost_on_reload` | After `reload`, a multi-step flow is back at step 1 with empty fields | Deterministic | #3 | 3.3.7 Redundant Entry |
| `no_resume_cue` | After coming back cold, the persona cannot tell which step it is on and redoes or skips a step | Deterministic | #1, #6 | 2.4.6 Headings and Labels |

**Seeded bugs:**

| ID | Pages | Bug | Clean version |
| --- | --- | --- | --- |
| B26 | `application-a/b` | The session expires after 10 minutes of inactivity with no warning, and all answers are lost | Warning at 8 minutes with "Stay signed in"; answers saved |
| B27 | `survey-a/b` | Answers to a 4-step survey are held only in JavaScript memory; a reload restarts it | Progress saved to `sessionStorage`; resumes at the same step |

---

## P10 Slow-connection user

**Config ID:** `slow_network` · **Axis:** Environment and perturbation

**Who it stands for:** people on 3G, in rural areas, on congested public Wi-Fi or on cheap data plans, and every user on a bad day. Slowness turns small design gaps into real errors, because people press again when nothing seems to happen.

**Use case:** "we get duplicate payments, but only from some users". The persona reproduces it: a 3-second response, no spinner, an impatient second press, two charges.

**Constraint:**

- Environment `network`: the harness adds latency to its own answer to the task's submission endpoint (it already answers it in `loop.py`), and can fail a set share of submissions (timeout or 503). Chromium network throttling (CDP `Network.emulateNetworkConditions`) is an option for whole-page slowness.
- Perturbation `impatient_retry`: if a submit click produces **no change in the tree within `after_ms`**, the harness clicks again at `rate`. The model didn't decide this; it is the slip people make.

```yaml
id: slow_network
environment:
  network:
    submit_latency_ms: 3000
    failure_rate: 0.2
perception:
  filters: [full_tree]
actions:
  allowed: [click, type, press, scroll, back]
  keys: [Tab, Enter, Escape]
memory:
  history_turns: 3
  max_steps: 20
perturbation:
  seed: 1234
  impatient_retry_rate: 0.6
  impatient_retry_after_ms: 1000
task_types: [complete_form]
```

**Realism basis:** response-time limits of 0.1 s, 1 s and 10 s (Miller, 1968; Card, Robertson and Mackinlay, 1991; Nielsen, *Usability Engineering*, 1993, chapter 5).

| Signal | Detector | Type | Nielsen | WCAG 2.2 |
| --- | --- | --- | --- | --- |
| `no_loading_feedback` | Between a submit and its response (≥ 1 s), no `aria-busy`, `progressbar`, `role=status`, disabled button or text change appears | Deterministic | #1 | 4.1.3 Status Messages |
| `duplicate_submission` | Reuses P1's detector; here it is triggered by impatience rather than a double press | Deterministic | #5 | 3.3.4 Error Prevention |
| `network_failure_silent` | The submission fails and nothing on the page says so; the persona assumes success or waits | Deterministic | #9 | 4.1.3 Status Messages |

**Seeded bugs:**

| ID | Pages | Bug | Clean version |
| --- | --- | --- | --- |
| B28 | `payment-a/b` | "Pay now" shows nothing for 3 s and stays enabled | Button disabled at once, with "Processing payment…" in `role=status` |
| B29 | `upload-a/b` | A failed submission leaves the page unchanged | "Couldn't send. Check your connection and try again." in `role=alert`, with a retry button |

**Note:** B4 (P1) and B28 both lead to duplicate orders, for different reasons. The report can contrast them as **the same symptom with two causes, separated by persona**.

---

## P11 Help-seeker

**Config ID:** `help_seeker` · **Axis:** Action space

**Who it stands for:** novices and anxious users who look for help, contact details or an FAQ when they get stuck. Research shows people seldom read help unprompted, but they do look for it once they fail. This is when help has to be easy to find.

**Use case:** a support team getting calls that the site could have answered. The persona tests whether, at the moment a user is stuck, help can be reached and is in the same place as on other pages. This covers **Nielsen #10** and WCAG 2.2's new **3.2.6 Consistent Help**.

**Constraint:**

- `escalation`: the harness detects being "stuck" deterministically: the same observation hash for `stuck_after` steps, or an error alert after two submits. The validator then accepts only `back`, `scroll`, `give_up` and `click` on refs whose name matches a version-controlled **help lexicon** (help, support, contact, FAQ, chat, "how do I", phone number, and so on, about 20 terms).
- After a help page is reached, normal actions come back with a budget of `after_help_steps`.

```yaml
id: help_seeker
perception:
  filters: [full_tree]
actions:
  allowed: [click, type, press, scroll, back]
  keys: [Tab, Enter, Escape]
  escalation:                  # proposed key
    stuck_after: 3
    mode: help_only
    lexicon: grounding/help_lexicon.yaml
    after_help_steps: 6
memory:
  history_turns: 3
  max_steps: 25
task_types: [complete_form, find_help]
```

**Realism basis:** Carroll and Rosson (1987), "Paradox of the active user"; Novick and Ward (2006), "Why don't people read the manual?", SIGDOC; the WCAG 2.2 Understanding document for 3.2.6.

| Signal | Detector | Type | Nielsen | WCAG 2.2 |
| --- | --- | --- | --- | --- |
| `help_unreachable` | Once in help-only mode, no help-lexicon ref is found within K steps | Deterministic | #10 | 3.3.5 Help (AAA) |
| `help_inconsistent` | Across pages in one flow, the help mechanism's position relative to other content (its order in the tree) changes, or it disappears | Deterministic | #10, #4 | 3.2.6 Consistent Help |
| `help_not_useful` | The persona reached help, came back, and still failed, while the baseline succeeds | Model-judged | #10 | 3.3.5 Help (AAA) |

**Seeded bugs:**

| ID | Pages | Bug | Clean version |
| --- | --- | --- | --- |
| B30 | `claim-a/b` | The policy-number format is never explained, and there is no help or contact anywhere on the form | A "Where do I find my policy number?" link next to the field |
| B31 | `support-1..3-a/b` | The "Contact us" link is in the header on page 1, in the footer on page 2 and missing on page 3 | In the same place on all three pages |

---

## P12 Habitual returning user

**Config ID:** `habitual` · **Axis:** Memory and perturbation

**Who it stands for:** regular users who work from habit, not by reading. They click where "Save" was last time. Jakob's Law: users spend most of their time on other sites and expect yours to work the same way.

**Use case:** a SaaS redesign where "Save" became "Apply" on one settings page and "Update" on another, and where the button in Save's old position now deletes. This covers **Nielsen #4** with an observed failure.

**Constraint:**

- `prior_knowledge`: a two-phase run. In phase 1 (familiarisation) the persona does the task on the **first page of the flow**. The harness records the accessible name and screen position of each control used for each kind of action (save, next, cancel). Phase 2 runs the remaining pages with this learned map shown as harness notes ("Last time you saved with 'Save changes', bottom right").
- Perturbation `capture`: Norman's **capture error**, where a strong habit takes over. When the model means to click a control and an element sits at the habitual position (or carries the habitual name), the click goes there instead at `capture_rate`. Both targets are logged.

```yaml
id: habitual
perception:
  filters: [full_tree]
actions:
  allowed: [click, type, press, scroll, back]
  keys: [Tab, Enter, Escape]
memory:
  history_turns: 3
  max_steps: 20
  prior_knowledge: familiarise_first_page  # proposed key
perturbation:
  seed: 1234
  capture_rate: 0.3            # proposed key
task_types: [repeat_task]
```

**Realism basis:** Norman (1981), "Categorization of action slips" (capture errors), already cited for P1; Reason (1990), *Human Error*; Nielsen (2000), Jakob's Law.

| Signal | Detector | Type | Nielsen | WCAG 2.2 |
| --- | --- | --- | --- | --- |
| `inconsistent_identification` | Controls that send the same request (same endpoint and method) have different accessible names on different pages | Deterministic | #4 | 3.2.4 Consistent Identification |
| `inconsistent_navigation` | The order of links in the shared navigation landmark changes between pages | Deterministic | #4 | 3.2.3 Consistent Navigation |
| `capture_consequence` | A capture slip activated a different function (for example a POST to a delete endpoint) | Deterministic | #4, #5 | 3.3.4 Error Prevention |

**Seeded bugs:**

| ID | Pages | Bug | Clean version |
| --- | --- | --- | --- |
| B32 | `settings-1..3-a/b` | The save button reads "Save", then "Apply", then "Update"; on page 3 "Delete" is where Save used to be | Same name and position on every page |
| B33 | `store-1..3-a/b` | The navigation order changes between pages | Fixed order |

The spec notes that #4 "can be checked deterministically, without a persona". That is true for the static inconsistency. The persona adds **consequence**: it shows the inconsistency causing a wrong action, which is what moves severity from 1 to 3 or 4.

---

## P13 Expert power user

**Config ID:** `power_user` · **Axis:** Budget and action space

**Who it stands for:** daily users of a tool: support agents, accountants, back-office staff. They want shortcuts, the Enter key and bulk actions, and every extra step costs them time hundreds of times a day.

**Use case:** an internal admin tool where archiving 10 tickets takes 30 clicks. The persona measures how far the real path is from the shortest one. This covers **Nielsen #7** using a number, not opinion.

**Constraint:**

- `budget: optimal_x`: each task in `tasks.yaml` gets `optimal_steps`, measured once by a scripted run on the clean page. The step cap is `ceil(optimal_steps × factor)`. The baseline keeps twice the persona's cap, as now.
- Actions include `press` with Enter and Tab, so an expert can submit from the keyboard if the page allows it.
- Cost reporting: each run is also scored with a Keystroke-Level Model time estimate (K, P, H, M operators), which gives an "expert seconds" figure for the report.

```yaml
id: power_user
perception:
  filters: [full_tree]
actions:
  allowed: [click, type, press, scroll, back]
  keys: [Tab, Shift+Tab, Enter, Escape, Space]
memory:
  history_turns: 6
  max_steps_factor: 1.5        # proposed key; max_steps = ceil(optimal_steps × 1.5)
task_types: [complete_form, bulk_task]
```

**Realism basis:** Card, Moran and Newell (1983), *The Psychology of Human-Computer Interaction* (GOMS and KLM); Nielsen's description of heuristic #7 (accelerators).

| Signal | Detector | Type | Nielsen | WCAG 2.2 |
| --- | --- | --- | --- | --- |
| `excess_steps` | The baseline succeeds in more than 2× `optimal_steps` while the persona hits its cap; the step ratio is reported | Deterministic | #7 | none (Nielsen only) |
| `no_enter_submit` | Enter in the last field of a form does nothing (no request) | Deterministic | #7, #4 | none (Nielsen only) |
| `no_bulk_action` | A task on N items needs N times the steps of one item | Deterministic | #7 | none (Nielsen only) |

**Seeded bugs:**

| ID | Pages | Bug | Clean version |
| --- | --- | --- | --- |
| B34 | `quickadd-a/b` | The fields are not inside a `<form>`, so Enter does nothing and the persona has to click | A real `<form>`; Enter submits |
| B35 | `bulk-a/b` | Archiving 10 items means 10 separate archive-and-confirm sequences | "Select all" and one confirmation |

---

## P14 Older adult (composite)

**Config ID:** `older_adult` · **Axes:** several, by design

**Who it stands for:** older adults with typical age-related changes that occur **together**: slower actions, reduced vision, less precise pointing, and more lapses under memory load. The population is large and growing, and it is under-served by single-issue testing.

**Use case:** a bank's online appointment booking that passes every single-persona run but fails older customers. Each step takes them longer, so a 60-second-per-page timeout hits, and the timeout warning's button is too small to press in time. **Only the combination finds it.**

**Why include it:** it shows the framework's axes **compose** without any new code beyond `think_time_s`. In the report it supports an evaluation question: *do combined constraints find failures no single persona finds?*

**Constraint:** a parameter bundle from existing axes.

```yaml
id: older_adult
environment:
  viewport: {width: 1280, height: 720}
  text_scale: 1.5
  think_time_s: 20             # page clock moves forward 20 s per step
perception:
  filters: [viewport_only]
actions:
  allowed: [click, type, press, scroll, back]
  keys: [Tab, Enter, Escape]
memory:
  history_turns: 2
  max_steps: 25
perturbation:
  seed: 1234
  typo_rate: 0.10
  mis_tap_base_rate: 0.05
  mis_tap_cap: 0.25
  mis_tap_reach_px: 8
task_types: [complete_form, multi_step_form]
```

**Realism basis:** Czaja, Boot, Charness and Rogers, *Designing for Older Adults* (3rd ed., 2019); Hawthorn (2000), "Possible implications of aging for interface designers", *Interacting with Computers*. **Every rate must be traced to a figure in these sources or labelled as our assumption.** This persona carries the highest risk of stereotyping (see Ethics below).

**Signals:** no new detectors. It reuses `timeout_no_warning`, `target_too_small`, `text_clipped`, `data_loss_on_error` and the others.

**Seeded bug:**

| ID | Pages | Bug | Clean version |
| --- | --- | --- | --- |
| B36 | `appointment-a/b` | Each step has a 60-second limit; the "Need more time?" prompt has a 20 px button and goes away after 10 s | 20-minute limit; the prompt stays until answered, with a large button |

**Expected result:** B36 is found by P14 but by **none** of P1 to P13 on their own. It is designed so that slow pacing alone (no mis-taps) or mis-taps alone (fast pacing) both pass.

---

## Coverage with P1 to P14

### Nielsen heuristics

| Heuristic | Before | After (new personas) | Strength |
| --- | --- | --- | --- |
| #1 Visibility of system status | P2 (partial) | P4, P5, P7, P9, P10 | Strong |
| #2 Match with real world | P3 | P8 | Strong |
| #3 User control and freedom | P1 | P6, P9 | Strong |
| #4 Consistency and standards | **none** | P4, P5, P11, P12 | Strong |
| #5 Error prevention | P1 | P6, P10, P12 | Strong |
| #6 Recognition rather than recall | P2 | P4, P9 | Strong |
| #7 Flexibility and efficiency | **none** | P13 (and P5) | Moderate |
| #8 Aesthetic and minimalist design | **none** | P8, P7, P4 | Moderate |
| #9 Recover from errors | P1 | P9, P10 | Strong |
| #10 Help and documentation | **none** | P11 | Moderate |

### WCAG 2.2 by principle

| Principle | Before | Added by P4 to P14 |
| --- | --- | --- |
| 1 Perceivable | none | 1.1.1, 1.3.1 (P4); 1.4.4, 1.4.10 (P7, P6) |
| 2 Operable | 2.4.2, 2.4.6 | 2.1.1, 2.1.2, 2.4.3, 2.4.7 (P5); 2.2.1, 2.2.5, 2.2.6 (P9); 2.4.1 (P4); **2.4.11** (P7); **2.5.8** (P6); 2.4.10 (P8) |
| 3 Understandable | 3.1.5, 3.3.1 to 3.3.4, 3.3.7 | 3.2.3, 3.2.4 (P12); **3.2.6**, 3.3.5 (P11) |
| 4 Robust | none | 4.1.2, 4.1.3 (P4, P10) |

Criteria in **bold** are new in WCAG 2.2, which is a good point for the report's novelty argument.

### Constraint axes

| Axis | Personas |
| --- | --- |
| Perception | P3, P4, P5, P7, P8 |
| Action space | P4, P5, P11, P13 |
| Memory and budget | P2, P9, P12, P13 |
| Perturbation | P1, P6, P10, P12 |
| Environment (new) | P6, P7, P9, P10, P14 |
| Composite | P14 |

## Changes to the evaluation protocol

The spec's protocol is unchanged: 3 conditions × 5 seeds, the attribution rule, k/5 stability. Additions:

1. **Persona-versus-static comparison (P4, P5).** On SB-01 to SB-05, report a "blocks task" column alongside axe-core and the keyboard sweep: of the static violations, how many stop a persona?
2. **Composition experiment (P14).** On B36, run each of P1 to P13 plus P14. Hypothesis: only P14 detects it.
3. **Same symptom, different cause (P1 against P10).** On B4 and B28, the duplicate-order symptom should be attributed to the right persona in each case.
4. **Cross-persona false positives.** Run every persona on every clean page, not only its own. This produces a 14 × 36 matrix, so check the cost (below) before running the full grid.
5. **Cost.** At about 15 to 25 steps per run, a full grid of 14 personas × 36 bug pairs × 3 conditions × 5 seeds is about 7,500 runs. The default plan is to run **each persona only on its own bugs** (about 1,100 runs) plus one full clean-page sweep at a single seed.

## Calibration: making the personas behave like real people

The spec lists "perturbation rates are chosen by us" as a limitation. Two ways to close it (pick one for FYP-2):

- **From the literature.** Take each rate (typo, mis-tap, retry) from a published figure, for example large-scale keystroke studies for typing errors (Dhakal et al., CHI 2018) and touch-target studies for mis-taps. Cite each one beside its config value.
- **From a small user study.** 6 to 8 participants do the same tasks on the clean test-app pages while the harness's logging records slips, back presses, retries and step counts. Fit the persona rates to these logs, then report **behavioural fidelity**: how closely persona runs match human runs on step count and slip distribution. This needs ethics approval, so start the form early.

## Ethics and limitations

- **No stereotypes.** P14 especially is a parameter bundle from published averages, not "what old people are like". The report should say that real people vary more than any persona does.
- **Personas don't replace users.** SimUX finds candidate failures cheaply and early. It does not replace testing with disabled users, and the report and the interface should say so.
- P4 models a screen reader's reading model, not a particular product. P6 has no gestures. P8's `skim_text` is a fixed cut, not real gaze.
- The help lexicon (P11) and `optimal_steps` (P13) are our own artefacts. Version them and report them.

## Build order

The order follows dependencies. Every persona is built; nothing is cut.

| Order | Work | Unlocks | Seeded pages |
| --- | --- | --- | --- |
| 1 | Environment axis: `device`, `viewport`, `text_scale`; bounding boxes in `RefMap` | P6, P7, P8 (partial) | — |
| 2 | Filters: `viewport_only`, `skim_text`, `linear_window`, `visible_focus_only`; interactive-roles-only validator | P4, P5, P7, P8 | B13 to B17, B20 to B25 |
| 3 | Perturbations: `mis_tap`, `impatient_retry`; network latency and failure on the submission route | P6, P10 | B18, B19, B28, B29 |
| 4 | Clock: `think_time_s`, `interruptions`; memory reset | P9, P14 | B26, B27, B36 |
| 5 | `escalation` and the help lexicon | P11 | B30, B31 |
| 6 | `prior_knowledge` and the `capture` perturbation | P12 | B32, B33 |
| 7 | `optimal_steps` in `tasks.yaml`, `max_steps_factor`, KLM scoring | P13 | B34, B35 |

New detectors: 30 signals, of which 28 are deterministic (`headings_not_descriptive` and `help_not_useful` are model-judged). Existing ones reused: `duplicate_submission`, the keyboard sweep's two detectors, `data_loss_on_error`.

## Open decisions

- [ ] **Supervisor sign-off** on extending from 3 to 14 personas. Record it in the Panel Action Register as scope growth. Present P1 to P3 as the core that is fully evaluated, and P4 to P14 as the extension.
- [x] Update the spec's Coverage section and Known limitations (the #4, #7, #8 and #10 limitation becomes "covered, moderate"). Coverage's extension column already named this; updated Known limitations' wording to match now that P4 to P14 are built (the full 5-seed evaluation is still outstanding, so "moderate" stands rather than being cleared).
- [ ] Add the Environment axis to the spec's framework table and flowchart.
- [ ] Choose the calibration route (literature or user study). A user study needs ethics approval.
- [ ] Contents of the help lexicon (P11) and how `optimal_steps` is measured (P13).
- [ ] Whether persona packs appear in the web interface's New Run screen.

All references above must be opened and checked by the author of the R&D section before they are cited, as the spec requires for P1 to P3.
