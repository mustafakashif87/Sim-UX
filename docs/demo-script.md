# Mid-eval demo script

Owner: Person A (drives the demo). Person B answers questions about the harness
and the detectors; Person C answers questions about grounding and the report.
Rehearsal: Wednesday night, end to end, with a timer. Target: 7 minutes plus
questions.

Items marked **TODO** depend on the LLM client and the recorded run, both due
Wednesday. Fill them in before the rehearsal.

## The one decision to make before rehearsal

P1's configured rates are low (`personas/error_prone.yaml`): a 10% chance of a
double press and 15% of a typo. With them, a live run on `order-a` usually
makes no mistake, so there is nothing to detect. Pick one approach and say it
out loud in the demo:

- **Demo rates (recommended):** run the demo with `double_submit_rate: 1.0` on
  the order pages and `typo_rate: 1.0` on the signup pages, as the detector
  tests do. Say: "For the demo we turn the mistake rate up to 1, so the slip
  happens on cue. The evaluation uses the configured rates, five seeds each."
- **Hunted seeds:** find a seed that triggers the mistake at the configured
  rate. It is more realistic, but the model's step count can change between
  runs and the seed may stop working on the day.

TODO (Person B): demo persona config or flag = __

## Before the panel arrives

- [ ] Test app opens: https://mustafakashif87.github.io/Sim-UX/ (or locally:
      `python -m http.server 8000 -d test-app`)
- [ ] `python test-app/check_seeds.py` prints `OK` (all bugs in place)
- [ ] Groq and Gemini keys loaded in the environment; one warm-up call each
- [ ] Recorded run open in a background tab (fallback 3)
- [ ] Fake-model fallback tested on this laptop (fallback 4, command below)
- [ ] Terminal and browser zoomed so the back row can read them
- [ ] Notifications off, laptop on power

## Running order

### 1. What SimUX is (45 s): `index.html`, then `test-app/SEEDED_BUGS.md`

> "SimUX tests a web page by giving an AI agent a real task and real limits.
> The limits are in code, not in the prompt. Our first persona is the
> Error-prone user: between what the agent decides and what the browser does,
> the harness injects human slips: a typo, a double press, a skipped field."

> "These are our test pages. Each comes in two versions that differ by exactly
> one line. Version A has a bug we planted on purpose; version B is the same
> page with that one line fixed. We wrote the list of bugs down before running
> anything."

### 2. P1 on `order-a`: a double press creates two orders (2 min)

> "The task is: place the order for the kettle. Watch the step log. Each step
> shows what the agent *intended* and what was actually *executed*."

- Run P1 on `order-a`. TODO: command = __
- Point at the step where intended = one click and executed = two clicks
  (perturbation `double_submit`).
- Point at the network log: two identical `POST api/orders` in the same step.
- Show the finding: `duplicate_submission`, Nielsen #5 Error prevention, WCAG
  3.3.4 Error Prevention, severity 3 (task done, but with harm).

> "The agent didn't decide to order twice. The page let a slip become two
> orders. That's a failure of the interface, not the agent."

### 3. The same on `order-b`: silent (1 min)

- Same persona, same seed, same slip.
- The second press finds the button disabled; one POST; **no finding**.

> "Same agent, same mistake. The only difference is one line of the page,
> `button.disabled = true`, and the finding disappears. That's how we know the
> page caused it."

### 4. P1 on `signup-a`, then `signup-b` (2 min)

> "Now a typo. The agent types the email; the harness swaps one character so
> it's invalid."

- `signup-a`: the error appears, **and the name field the agent already filled
  is wiped**. Finding: `data_loss_on_error`, Nielsen #9, WCAG 3.3.7 Redundant
  Entry.
- `signup-b`: same typo, the error appears, the name stays. **No finding.**

> "The one-line difference here is `form.reset()` on error."

### 5. What a scanner sees (45 s): `logs/README.md`

> "We also ran axe-core, the standard accessibility scanner, on every page. It
> catches the three static bugs: missing alt text, an unnamed button, an
> unlabelled field. It reports **nothing** on the keyboard trap, the mouse-only
> control, or any of B1 to B6. Those only show up when someone actually tries
> to use the page. That's the gap SimUX is for."

### 6. Where we are (30 s)

- Built: the persona framework, P1 end to end, two detectors, the seeded test
  app with CI checking every bug on every push, deployed to GitHub Pages.
- Next: the remaining P1 detectors, the 3-condition × 5-seed evaluation, then
  P2 and P3.
- Known gap: B6 (asking again for an address) has a page but no detector yet.

## Fallback ladder

Move down one rung when a call errors twice or takes more than ~20 s. Say so
plainly: "The API is slow right now, so I'll switch to…". Never present a
fallback as live.

| Rung | What | How |
| --- | --- | --- |
| 1 | Groq, live | TODO: command / env = __ |
| 2 | Gemini, live | TODO: command / env = __ |
| 3 | Replay of the recorded run (`order-a`, `signup-a`, recorded Wed with Person B) | TODO: path `logs/demo/<run_id>/`; show `steps.jsonl` (intended vs executed) and the findings |
| 4 | Fake model, offline, no key | `pytest -v tests/e2e/test_test_app.py --override-ini addopts=`: shows each detector firing on the buggy page and silent on the clean one, plus a careful user succeeding on both signup pages. Tested: 6 passed in 13 s |

Rungs 3 and 4 still show real pages, real logs and real detectors; only the
model's choices are replayed or scripted.

## Questions Person A should be ready for

**Why does each buggy/clean pair differ by exactly one line?**
So the attribution rule works: a finding counts only if it fires on the buggy
page and not on the clean one. If the pages differed in anything else, a
difference in outcome could come from that instead. Show `diff order-a.html
order-b.html` (one line: `button.disabled = true`) and `diff signup-a.html
signup-b.html` (one line: `form.reset()`).

**Why are the file names `-a` and `-b`, not "buggy" and "clean"?**
The persona's observation includes the URL path. A name like `buggy-order.html`
would tell the agent where to look. Page text, IDs and class names are neutral
for the same reason; the bug is named only in `SEEDED_BUGS.md`.

**How do you know the bugs are really there?**
`check_seeds.py` checks every bug on every push, as a required CI check: present
on version A, absent on version B. It also drives each task to its goal on
both versions, so a failure can't come from a broken page.

**Why do the pages need HTTP?**
They submit with `fetch` to a relative `api/` URL, which browsers block on
`file://`. The harness answers that URL itself, so runs don't depend on where
the pages are hosted.

**Why keep SB-01 to SB-05 if the keyboard persona was dropped?**
They're fixtures for the deterministic layer: axe-core finds SB-01 to SB-03, and
the planned keyboard sweep covers SB-04 and SB-05, which axe misses.

**What about B6?**
It's a real seeded bug (WCAG 3.3.7) with a page pair and a check, but no P1
detector yet. It's reported as a known gap for mid-eval and planned next.
