# POC_SPEC.md — SimUX FYP-I Proof-of-Concept Specification

Produced by an interview process (see conversation log) that treated every
"looks obviously right" call as a decision to surface, not assume. This
document is the settled result. Pair with `DESIGN.md` (visual tokens) and
the earlier architecture-review notes on what's reusable from Site Doctor.

---

## 1. What this POC is, in one sentence

A static, fully click-through visual prototype of the finished SimUX
product — for the FYP-I panel presentation, where the ask is "show us
what you're going to build," not "prove it works." **Nothing executes.
No agent runs, no LLM is called, no browser is launched, no computation
happens.** Every screen shows real-looking dummy data that depicts what
the end-of-FYP-II system will do.

## 2. Governing rules (apply to every decision below, no exceptions)

1. **Zero backend calls at runtime.** No Playwright, no LLM API, no
   real computation of any kind during the demo. This was tightened
   twice during scoping — an earlier idea to keep one real browser
   launch, and a later idea to let the deterministic UI-Score half run
   for real, were both explicitly rejected. Static means static.
2. **Dummy data throughout** — no real target site, no real crawl. A
   fictional product name and mocked-up screenshot graphics stand in
   for "a page," styled per `DESIGN.md`.
3. **Citations are the one place "dummy" does not mean "fabricated."**
   Any WCAG success criterion or Nielsen heuristic text shown on
   screen must be genuine, correctly quoted — hand-picked, not
   retrieved, but never invented. This is non-negotiable: faking a
   citation inside a demo of an anti-hallucination feature is a
   uniquely bad failure mode if caught.
4. **Built for extension, not thrown away.** Real components/routes
   per module, one typed fixture-data seam (`useDemoRun()`-style) that
   later swaps for a real fetch call, and stage-naming in the code that
   mirrors the eventual LangGraph node names (crawl → detect → ground
   → fix → sandbox → verify → aggregate).
5. **Honest maturity gradient, not uniform polish.** Detection,
   Grounding, and the fix→sandbox→verify showcase get full, detailed,
   interactive-feeling treatment. Correction/Learning gets a visibly
   simpler, explicitly "planned for FYP-II" card — not faked at the
   same fidelity as everything else.
6. **No PDF report, no real target URL required of you.** The "report"
   is an in-app screen only; nothing needs to be generated.

## 3. Build substrate

Extend Site Doctor's existing React frontend and component library
(the `card-chart` visual system, `SeverityTag`, `Trace`, motion
patterns) — not the SEO/security backend logic, which is deleted, not
hidden, per the earlier reuse analysis. No FastAPI/LangGraph execution
is wired up for this POC; the graph's *shape* (node names, edges)
informs the fixture's stage vocabulary and the running-animation
sequence, but the graph itself does not run.

## 4. Personas shown

All three from the proposal, at these depths:

| Persona | Depiction | Depth |
|---|---|---|
| Accessibility-focused | Blurred/desaturated screenshot beside a plain linearized text list (stands in for "sees only the accessibility tree, never the screenshot/DOM/CSS") | Full — one showcase finding |
| Motor/age-related | Sharp screenshot with an animated cursor that misses a small target, then corrects | Full — one showcase finding |
| Mobile-first | Shown as a real card in the persona-selection screen, but visibly badged "Phase 2 / FYP-II" | Placeholder only — matches the proposal's own "cut first if behind schedule" framing, so the demo doesn't contradict its own source document |

## 5. Demo scenario

A fictional product (invented name, e.g. a small storefront/signup
flow), depicted through mocked-up screenshot graphics built to
`DESIGN.md`'s visual language — not a real running site, not a real
crawl. Two illustrated "tasks" anchor the fixture content across
screens: a signup flow and a checkout flow, so findings have a
consistent, plausible narrative home rather than reading as
disconnected placeholder text.

## 6. Screens and demo flow

One narrated flow, not six separate module screens (screens read as
*more* unfinished when they're thin and empty; one coherent narrative
reads as an architecture story even with nothing behind it):

1. **Landing** — rewritten from scratch (Site Doctor's current landing
   copy describes a different, bundled SEO+UX+Security product and
   must not survive in any form). Big serif headline per `DESIGN.md`,
   short conversational subhead, three-persona framing in place of
   Site Doctor's three-audience framing.
2. **New run / persona selection** — large, soft-radius persona cards
   (not small checkbox toggles — the checkbox-list metaphor is the
   single most Site-Doctor-coded interaction pattern in the current
   app and must not carry over). Each card states its actual
   restriction in plain language and shows its visual metaphor at rest
   (a small blurred thumbnail on the accessibility card, a jittering
   cursor icon on the motor card).
3. **Running / execution state** — the animated stage-by-stage
   walkthrough (crawl → persona attempts → grounding cites a source →
   fix proposed → sandbox → verify → aggregate), using blur/desaturate
   intensity and cursor-jitter as the literal visual for "this agent
   cannot see this" / "this agent moves imprecisely" while it plays.
   This is the single screen doing the most work to communicate the
   Agent + Execution Layer's actual novelty claim, since nothing
   underneath it is real.
4. **Results / Aggregation dashboard** — severity-grouped findings
   (reusing `IssueCard`/`UxSuggestionCard`'s existing layout), **persona
   as a first-class grouping/filter alongside severity**, a hero-scale
   UI Score number (big serif numeral, `DESIGN.md`'s "pricing number"
   pattern) with the Visual Design / Accessibility-Visual breakdown
   underneath, and a short fake run history (2–3 prior dummy runs)
   depicting regression comparison.
5. **Finding detail (one showcase per full-depth persona, two total)** —
   the full fix → sandbox → verify walkthrough: a proposed fix, a
   labeled "sandboxed copy" panel, and a pass/fail verification stamp
   (the hard "sticker shadow" treatment from `DESIGN.md` specifically
   for the *pass* state — a literal stamp metaphor). Only accessibility
   and motor/age get a showcase — mobile-first is placeholder-only
   (§4), so a showcase for it would contradict its own "Phase 2"
   framing. Every other finding in the results list is a plain,
   already-triaged card with no animated walkthrough — the showcase
   stays concentrated and rehearsable rather than diluted across
   repeats.
6. **Correction/Learning** — not a screen with fake interactivity. A
   single simple panel/diagram, explicitly labeled "planned for
   FYP-II," describing the case-store concept in one or two sentences.
   Deliberately the least-polished surface in the app.

## 7. What this POC must NOT do (risk guardrails)

**Claims not to make out loud or implicitly:**
- Never say or imply anything "detects," "verifies," or "learns" during
  the live demo — say "here's how this will work" / "this is what the
  system will show," not "watch it find this."
- Never claim the citations shown were *retrieved* — say they're
  real WCAG/Nielsen text used to illustrate what grounded output will
  look like.
- Never claim the UI Score number reflects a real computation.

**What would make this look like Site Doctor instead of SimUX:**
- Carrying over the "pick checks to run" (SEO/UX/Security) mental
  model instead of "pick personas."
- Leaving any literal "Site Doctor" branding, copy, or the
  screenshot-plus-roleplay-prompt "UX review" framing anywhere —
  that pattern is specifically what SimUX's own lit review calls
  insufficient, so it's the highest-risk leftover if not fully removed.
- A landing page that still pitches a bundled SEO+UX+Security tool.

**What would make this academically weak:**
- Fabricated citation text (see rule 3).
- Uniform, equally-polished treatment across all six modules, which a
  panel can catch by comparing against your own Table 2.3 timeline.
- No visible acknowledgment anywhere in the demo that this is a
  prototype of end-state, not working software.

**What would make the demo impressive but misleading:**
- Animating the fix→verify walkthrough in a way that implies it ran
  automatically/live rather than being a scripted sequence.
- Showing the persona "restriction" purely as a label/badge with no
  visual consequence (a checkbox that says "accessibility mode" but
  the screenshot looks identical to every other persona) — the
  blur/jitter metaphors exist specifically so the restriction has a
  *visible* effect, which is the whole point being depicted.

**Likely panel challenges, and the honest answer ready for each:**
- *"Is any of this actually running?"* → No — this is a click-through
  prototype of the end state; the real pipeline is FYP-II's scope per
  our own Table 2.3.
- *"Why does mobile-first look unfinished compared to the other two?"*
  → Matches our own proposal's stated cut-first priority.
- *"Where did this citation come from?"* → Hand-picked from the real
  WCAG/Nielsen source, not retrieved — the real Grounding Layer's
  retrieval mechanism is FYP-II scope.
- *"Why does Correction/Learning look so much thinner than the rest?"*
  → It's the least mature module in our own plan; we chose not to fake
  polish we haven't earned yet.

## 8. Explicitly deferred to later iterations (not this POC)

Real Playwright execution, real LLM calls (open-weight stack per the
proposal's Section 2.3, not OpenAI — settled but moot until real calls
exist), real WCAG/Nielsen retrieval corpus, real sandbox-apply-reverify
logic, real embedding-similarity case store, the actual seeded-bug
test application, and any FastAPI/LangGraph execution at all.
