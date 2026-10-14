# Mid-eval demo script

Owner: Person A (drives the demo). Person B answers questions about the harness
and the detectors; Person C answers questions about grounding and the report.
Rehearsal: Wednesday night, end to end, with a timer. Target: 7 minutes plus
questions.

The whole demo is one command, from the repo root with the venv active:

```bash
python -m agent.demo            # live: real model, browser visible
python -m agent.demo --replay   # fallback: the recorded runs, no network
```

It runs P1 on `order-a`, `order-b`, `signup-a` and `signup-b` with the seeds
below, pausing for Enter between pages, and ends with one table: page, mode
(LIVE or REPLAY), finding, and whether it matches the ground truth. Each page
prints every step's intended and executed action, then the findings. The
browser is visible and slowed down so the panel can follow it. The key is read
from `.env`.

If a live run fails (no key, quota, network: 2 attempts and 20 s a call at
most), the demo stops and prints the command to continue with, for example
`python -m agent.demo --replay --from signup-a`. It never switches to the
recording by itself. Pages that ran live keep their live result.

One page on request ("show us signup-b again"):
`python -m agent.run --page signup-b --seed 69 --logs logs/demo --headed`.

## Seeds: decided

P1's configured rates are low (`personas/error_prone.yaml`), so a single live
run with an arbitrary seed usually makes no mistake and there is nothing to
detect. The demo uses seeds chosen in advance, at the configured rates (no
rate is turned up):

| Pages | Seed | What the seed does |
| --- | --- | --- |
| `order-a`, `order-b` | **1** | Doubles the first click (`double_submit`) |
| `signup-a`, `signup-b` | **69** | Skips the email field on step 1 (`skip_field`), then no other mistake |

Say so if asked: "we picked these seeds so the slip happens on cue; the
evaluation uses seeds 1 to 5 on every page and reports k out of 5." Seed 1 is
also the evaluation's first seed.

Seed 37, used in the dry run with the scripted model, no longer fits: with the
real model it took 16 steps on `signup-a` and picked up a typo and a double
press on the way. Recorded with `groq/openai/gpt-oss-120b` on 14 Oct; all four
runs are in `logs/demo/`:

| Page | Seed | Steps | Finding |
| --- | --- | --- | --- |
| `order-a` | 1 | 1 | `duplicate_submission`, severity 2 |
| `order-b` | 1 | 1 | none |
| `signup-a` | 69 | 6 | `data_loss_on_error`, severity 3 |
| `signup-b` | 69 | 5 | none |

## Before the panel arrives

- [ ] Test app opens: https://mustafakashif87.github.io/Sim-UX/ (or locally:
      `python -m http.server 8000 -d test-app`)
- [ ] `python test-app/check_seeds.py` prints `OK` (all bugs in place)
- [ ] `.env` in the repo root holds `LLM_API_KEY` (Groq); it is git-ignored and
      read automatically. Never open it on the projector.
- [ ] Once per laptop: `source .venv/bin/activate` then
      `playwright install chromium`. The demo shows the full browser; the
      setup in the README installs only the headless one.
- [ ] `python -m agent.demo --check` ends with `Ready.`: one live call to the
      model, and all four recordings replayed with the expected findings
      (writes nothing to `logs/demo`); it also opens the visible browser once
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

- Start `python -m agent.demo`; it opens with `order-a`.
- Point at the step where intended = one click and executed = two clicks
  (perturbation `double_submit`).
- Point at the network log: two identical `POST api/orders` in the same step.
- Show the finding: `duplicate_submission`, Nielsen #5 Error prevention, WCAG
  3.3.4 Error Prevention, severity 2. The rule (`grounding/ground.py`): 4 if
  the task failed, 3 if it was completed with data loss, otherwise 2. The
  order went through, and nothing the user entered was lost.

> "The agent didn't decide to order twice. The page let a slip become two
> orders. That's a failure of the interface, not the agent."

### 3. The same on `order-b`: silent (1 min)

- Press Enter: `order-b` runs.
- Same persona, same seed, same slip.
- The second press finds the button disabled; one POST; **no finding**.

> "Same agent, same mistake. The only difference is one line of the page,
> `button.disabled = true`, and the finding disappears. That's how we know the
> page caused it."

### 4. P1 on `signup-a`, then `signup-b` (2 min)

> "Now a lapse. The agent fills in the form, but the harness leaves one
> required field empty, as a person who forgot a field would. The page should
> say what's missing and keep everything else."

- Press Enter for `signup-a`, then again for `signup-b`. Then show the
  summary table.
- Seed 69 on both pages, so the same field is skipped at the same step.
- Point at step 1: the intended action typed the email; the executed action
  is `(nothing)` (perturbation `skip_field`).
- `signup-a`: the error appears, **and the field the agent did fill is
  wiped**, so the agent types the name again (step 4). Finding:
  `data_loss_on_error`, severity 3, Nielsen #9, WCAG 3.3.7 Redundant Entry.
- `signup-b`: same skipped field, the error appears, the filled field stays;
  the agent only adds the email. **No finding**, one step shorter.

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
| 1 | Groq, live: `openai/gpt-oss-120b`, an open-weight model | `python -m agent.demo`. A failed call is retried once; then the demo stops and prints the next command |
| 2 | Groq, live, another open-weight model | `LLM_MODEL=qwen/qwen3.8-27b python -m agent.demo --from <page>`. Answers a test call; not rehearsed on the demo pages, so the seeds may not trigger the same steps |
| 3 | Replay of the recorded runs (all four pages, 14 Oct) | `python -m agent.demo --replay --from <page>`, as printed on failure. No API call; the page, harness and detectors still run for real. The output says `REPLAY`, and `run.json` records `"replay": true` |
| 4 | Fake model, offline, no key | `pytest -v tests/e2e/test_test_app.py --override-ini addopts=`: shows each detector firing on the buggy page and silent on the clean one, plus a careful user succeeding on both signup pages. Tested: 6 passed in 13 s |

Rungs 3 and 4 still show real pages, real logs and real detectors; only the
model's choices are replayed or scripted.

A live run never reads the recording: it always calls the API. Only
`--replay` reads `logs/demo/llm-cache/`, so a replay cannot pass as live.

OpenRouter (`LLM_PROVIDER=openrouter`) is supported by the client but has no
key or test run yet; add it as a rung only after one rehearsed run.

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
