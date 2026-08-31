# SimUX POC — Milestone Build Plan

This is the living, detailed build plan for the SimUX POC (the FYP-I
click-through prototype — see `POC_SPEC.md` for what that means and why).
It originated as a Claude Code plan document and is reproduced here in
full, in the project repo, so it stays with the code and stays current.
For a shorter "what's done / what's left" summary, see `CLAUDE.md` §10;
this file is the detailed reference behind that summary.

## Context

`site-doctor/` is an existing, broader multi-purpose auditing tool (SEO +
UX + security) that predates SimUX. SimUX is a separate Final Year
Project — a multi-persona UI/UX auditor built around six architectural
modules (Agent, Execution, Remediation, Grounding, Correction/Learning,
Aggregation) — none of which exist as working software yet.

The immediate need is a **POC for the FYP-I defense presentation**,
where the ask is "show us what you're going to build," not "prove it
works." This was pinned down precisely over a long interview (captured
in `POC_SPEC.md`): it must be a **100% static, fully click-through
visual prototype**. Nothing executes — no agent runs, no LLM is called,
no browser launches, no computation happens. Every screen shows
realistic dummy data depicting the end-of-FYP-II product's final look
and flow, built so real functionality can be layered in later without a
rewrite (one typed fixture-data seam, component/route names matching the
six modules, stage-naming matching the eventual LangGraph nodes).

Two governing documents are the source of truth alongside this one:
`POC_SPEC.md` (what to build, what must never be faked — real
WCAG/Nielsen citation text, an honest maturity gradient across modules,
explicit risk guardrails) and `DESIGN.md` (the visual language — colors,
type, motion, the scroll-pinned section patterns — now describing the
current implemented system, not just the original research it grew from).

**One spec correction made during the original planning pass:**
`POC_SPEC.md` §6 item 5 said "one showcase per persona, three total,"
which contradicted §4's own persona-depth table (mobile-first =
"Placeholder only"). Resolved: **two showcases** (accessibility +
motor/age). Mobile-first gets no fix→sandbox→verify showcase, consistent
with its "Phase 2" badge everywhere else it appears.

---

## Status at a glance

| Milestone | Status |
|---|---|
| M0 — Scaffold parity | ✅ Done |
| M1 — Design tokens | ✅ Done |
| M2 — Shared primitives | ✅ Done |
| M3 — Fixture-data seam, citations | ✅ Done |
| M4 — Routing shell and app frame | ✅ Done |
| M5 — Persona-restriction + verify-stamp visual spike | ✅ Done |
| M6 — Landing screen (full rewrite) | ✅ Done |
| M6b — Landing v2 (Wispr-referenced redesign) | ✅ Done |
| M6c — Landing animation overhaul | ✅ Done |
| M7 — New-run / persona-selection screen | ✅ Done |
| M8 — Running / execution state | ✅ Done |
| M9 — Results / Aggregation dashboard | ✅ Done |
| M10 — Finding detail (fix→sandbox→verify showcase ×2) | ✅ Done |
| M11 — Correction/Learning panel | ✅ Done |
| **M12 — End-to-end rehearsal + risk-guardrail audit** | ✅ **Done** |

**The M7 gate is lifted, and M8 through M12 are now all done.** The plan
originally read "M7 does not start until M6c lands and the user
confirms the landing page's design philosophy is settled." That
confirmation was given explicitly ("start M7"), M7 was built and
verified, and M8/M9/M10/M11/M12 were each separately approved to start
("yes go ahead"/"start m11"/"start m12") and are also built and
verified. **The full six-screen POC (M0–M12) is complete** — every
milestone in this plan is built, verified, and documented.

---

## Status as of this revision (detailed)

M0–M12 are built and verified (build clean, zero type errors, no
leftover Site Doctor branding). Several things changed after the
original plan was written that make parts of the milestone text below
stale — noted inline where relevant, and summarized here:

1. **The clinical-instrument visual metaphor was removed entirely**,
   on top of the original plan. Site Doctor's graph-paper grid
   background, the ECG/vitals-trace motif (`Trace.tsx` and its
   `animate-blip` keyframe), and the "monitor band" language are all
   gone — deleted, not hidden. `BrandMark`'s icon is three dots (one
   per persona) instead of an ECG line. **M8's own text below still
   says "reuse `Trace.tsx` as the pipeline spine" — that file no
   longer exists; M8 needs a non-clinical replacement for that spine
   visual when it's built (a simple connecting line/dot-progression,
   not a waveform).**
2. On the persona cards (built in M6's `PersonaShowcase`, reused by
   M7): the mobile-first card's opacity dimming was removed and its
   hover interaction was made identical to the other two personas —
   only the "Phase 2 · FYP-II" badge distinguishes it, not reduced
   visual/interactive polish. **M7 applied this same rule when building
   the real selection cards** — mobile-first is genuinely selectable
   there too, not just present-but-inert (see M7's detailed entry below).
3. **M6c grew substantially beyond its original scope.** What started
   as "replace generic fade+rise motion with something purposeful" became
   two full structural rebuilds:
   - `CapabilityGrid.tsx` ("Four things every report actually has")
     went through several different sticky-panel architectures before
     landing on the current one — including finding and fixing a real
     Chromium bug (`position: sticky` silently breaking when there's a
     plain wrapper `<div>` between the sticky element and its
     positioned containing-block ancestor), and deriving — not
     guessing — the exact geometry so the panel's lock point precisely
     matches the first block's top and its release point precisely
     matches the last block's bottom (both verified pixel-exact via a
     Playwright probe reading real `getBoundingClientRect()` values,
     not eyeballed).
   - `PipelineStages.tsx` ("How it works") was fully rebuilt from a
     static 7-card grid into a scroll-pinned, 7-stage product
     walkthrough built entirely on `motion/react` (no GSAP added, a
     deliberate choice — see `CLAUDE.md` §4), grounded in one real
     fixture finding moving through the whole pipeline rather than
     seven unrelated illustrations.
   - Both fixes and the full reasoning behind them are documented in
     `CLAUDE.md` §6 (bug table) and §§8–9 (per-component deep dives) —
     read those before touching either file again.
4. **M7 deviated deliberately from this plan's own literal text** (see
   M7's entry below for the full reasoning) — built as multi-select
   (`ToggleGroup type="multiple"`), not the single-select "radio-group"
   originally specified, because the product's own concept (multiple
   personas per run, findings aggregated together) contradicts
   single-select.

This revision folds all of that in and marks M7 complete. M8 onward is
otherwise unaffected and still follows the original plan below except
where a note flags a staleness (M8's `Trace.tsx` reference).

---

## M0 — Scaffold parity with the sibling project ✅ Done

- Init Vite 6 + React 18 + TS 5.7 at `simux-poc/`. Recreate `package.json`
  with the exact dependency versions audited from
  `site-doctor/frontend/package.json` (Radix checkbox/collapsible/label/
  separator/switch, `motion` 12.x — imported as `motion/react`, not
  `framer-motion` — `react-router-dom` 6.28, `class-variance-authority`,
  `clsx`, `tailwind-merge`, `lucide-react`, Tailwind 3.4 +
  `tailwindcss-animate`).
- Recreate `vite.config.ts` with the `@` → `./src` alias, but **drop the
  `/api` proxy block** — there is no backend to proxy to, and leaving
  dead proxy config in is a small but avoidable "does this actually
  call something?" red flag if anyone reads the repo.
- Recreate `tsconfig.json` / `tsconfig.app.json` / `tsconfig.node.json`
  with the same `paths` mapping and strict flags (Vite doesn't read
  tsconfig paths automatically — both files need the alias).
- Recreate `index.html`: same Google Fonts `<link>` tags (Archivo, IBM
  Plex Mono, Source Serif 4, same weights), but a **new title, meta
  description, and favicon** — no Site Doctor branding, even transiently.
- **Verify:** `npm install && npm run dev` serves a blank page with no
  console errors at `localhost:5173`; `npm run build` succeeds with zero
  type errors; page source shows the new title/meta/favicon.

*(Archivo was later swapped for Bricolage Grotesque in M6b/M6c — see
`DESIGN.md` §2.)*

## M1 — Design tokens: port, then apply DESIGN.md's adaptations ✅ Done

- Port `index.css`'s `:root` block and `tailwind.config.js`'s `extend`
  block verbatim as the starting point (paper/stock/ink/rule/severity
  HSL triples, `card-chart`/`label-mono`/`rule-perf`, the grid
  `body::before`, `d1/d2/d3` font sizes, `sweep`/`blip`/collapsible
  keyframes).
- Apply DESIGN.md's deltas as **named overrides**, not silent edits:
  - Warmer/creamier `--paper` than the sibling's current desaturated
    grey-green.
  - Two-tier `borderRadius`: keep existing `sm`/`md`/`lg` tight for
    buttons/tags/inputs; add new `xl`/`2xl` tokens (24–40px) reserved
    for section-level containers only.
  - A new zero-blur "stamp" shadow token for the verify-pass badge.
  - Four new pastel tint tokens for personas, chosen to sit clearly
    outside the existing severity hues.
- **Fix the heading-font conflict directly, not by assumption.** Resolved:
  un-force `font-display` at the base layer for hero-scale headings;
  apply a serif specifically to hero-scale `d1`/`d2` headings via a
  class; keep `font-display` as the default for smaller in-card headings.
- **Verify:** a temporary, dev-only token/swatch page (`/dev/tokens`,
  `import.meta.env.DEV`-gated) renders every token for visual check.

*(The exact `--paper` value was revisited once more in M6b — see
`DESIGN.md` §1 — to the exact HSL conversion of RGB 255,255,237.)*

## M2 — Shared primitives: port and deliberately adapt ✅ Done

- Copy file-by-file (hand-written originals, not shadcn-regenerated):
  `ui/{button,checkbox,collapsible,input,label,separator,skeleton,switch}.tsx`,
  `lib/utils.ts`, `lib/motion.ts`, `SeverityTag.tsx`, `Trace.tsx`,
  `CountUp.tsx`, `SectionHeading.tsx` as-is.
- **Adapt `button.tsx`'s hover, don't copy it as-is.** Changed from
  lift-up (`hover:-translate-y-0.5`) to press-down (`scale(0.98)` on
  `:active`), per `DESIGN.md`'s Wispr-derived motion rule.
- **State the `label-mono` rule once, in a comment at its definition:**
  uppercase mono for genuinely code-like content only; sentence-case
  tracked-sans (`.eyebrow-sans`) everywhere else.
- **Decide the tint-collision rule now:** persona-grouped views use
  persona tint exclusively; severity/plain views keep the neutral
  `stock` rotation. The two tinting systems never apply to the same card.
- Keep Radix checkbox/switch in the port for later accessible-selection
  use.
- **Verify:** extend the M1 token page with every primitive rendered.

*(`Trace.tsx` was later deleted entirely post-M4 — see "Status as of
this revision" above.)*

## M3 — Fixture-data seam, stage vocabulary, citation content ✅ Done

- Define the typed fixture-data module and `useDemoRun()` as the one
  seam between data and every screen.
- Name pipeline stages in code exactly as the eventual LangGraph nodes:
  `crawl`, `detect`, `ground`, `fix`, `sandbox`, `verify`, `aggregate`.
- Invent the fictional product name ("Marlow") and the two anchor tasks
  (signup flow, checkout flow) that all dummy findings hang off.
- **Hand-transcribe genuine WCAG success-criterion text and genuine
  Nielsen heuristic text**, verbatim from the real W3C WCAG spec and the
  real NN/g heuristics list — never paraphrased, never invented. Source
  noted in a comment in `lib/fixtures/citations.ts` for the M12 re-check.
- **Verify:** a throwaway dev route (`/dev/fixture`) dumps `useDemoRun()`'s
  full output; each citation string checked against its real source.

## M4 — Routing shell and app frame ✅ Done

- `App.tsx` routes for all six screens (landing, new-run, running,
  results, finding-detail, correction) plus a catch-all to landing.
- Rebrand `SiteNav.tsx`/`Footer.tsx` so every screen has consistent chrome.
- **Verify:** click every nav link/route by hand — each reaches a real
  (even if placeholder) screen, no console errors, no leftover Site
  Doctor nav/footer text anywhere.

*(Everything past Landing and NewRun is still this milestone's
placeholder, by design, until its own milestone (M8-M11) is built.)*

## M5 — Novel visual-metaphor spike: persona restriction + verify stamp ✅ Done

De-risked early, deliberately before any full screen — these have no
precedent anywhere in the sibling project.

- Accessibility "restricted view": a screenshot graphic behind
  `backdrop-filter: blur()` + desaturate, beside a plain linearized text
  list — built at both a small "at rest" (card thumbnail) intensity and
  a full "running" intensity. → `AccessibilityRestrictedView.tsx`
- Motor "imprecise input": an animated cursor that overshoots/misses a
  small target, pauses, then corrects — at both icon scale and full
  animated scale. → `MotorImprecisePointer.tsx`
- The hard-shadow "stamp" pass/fail badge. → `VerifyStamp.tsx`
- **Verify:** an isolated dev route (`/dev/metaphors`) renders all three
  at both scales; confirms `prefers-reduced-motion` is respected.

## M6 — Landing screen (full rewrite) ✅ Done

- Rebuild `Landing.tsx` reusing the sibling's section rhythm (hero →
  persona cards → pipeline-stage trace → closing → final CTA) with
  entirely new content — persona framing replaces audience framing.
- Apply M1's corrected serif hero treatment and generous section padding.
- **Verify:** confirm no shared copy or "checks"-framing with the old
  landing page; hero reads persona-first; `tsc --noEmit` clean.

## M6b — Landing v2: Wispr Flow-referenced redesign ✅ Done

Prompted by a reference screenshot of wisprflow.ai's actual marketing
page and explicit dissatisfaction with M6's first pass.

Three integrity forks, resolved explicitly:

- Wispr's customer-logo strip → **a "Grounded in real standards" strip**
  naming W3C/WCAG 2.2 and Nielsen Norman Group instead — text
  wordmarks, not fabricated logos. → `GroundedInStandards.tsx`
- Wispr's testimonials (real named people) → **dropped entirely.** No
  fabricated quotes.
- Wispr's interactive hero toggle → **kept, and made real**: an actual
  toggle in the hero swaps the specimen card between a normal view and
  `AccessibilityRestrictedView` — genuine component state. → `Hero.tsx`

New/changed sections, in page order: Hero (with toggle) →
Grounded-in-standards strip → PersonaShowcase → Comparison (real
qualitative differences, no invented numbers) → PipelineStages →
ConcernCloud (real concern tags + real stakeholders from the proposal)
→ CapabilityGrid (four small cards) → FinalCta → Footer (two columns +
large wordmark).

- **Verify:** every new section reads correctly against `useDemoRun()`
  fixture data; grep confirms no fabricated statistic, no
  testimonial-shaped content, no unearned "used by" claim; `tsc
  --noEmit` clean.

## M6c — Landing animation overhaul: purposeful motion, not generic reveal ✅ Done

Trigger: the shared fade+rise+stagger variants were applied almost
everywhere as a blanket default — called out directly as reading like
the single most recognizable generic template motion pattern.

Section-by-section (all implemented):

1. **Hero** — mount-triggered underline sweep beneath the italic
   emphasis line, reusing the `ruleVariants` self-draw pattern.
2. **GroundedInStandards** — each name's underline draws in *after* it
   appears, reading as "this is being verified."
3. **PersonaShowcase** — the restriction visuals now trigger for real
   once each card scrolls into view (`active` prop added to both M5
   metaphor components, default preserving every existing call site's
   behavior) — the restriction demonstrates itself instead of being
   pre-rendered in its end state.
4. **Comparison** — check/X icons draw in via SVG `pathLength: 0→1`,
   reading as "being marked."
5. **PipelineStages** — **full rebuild**, not just new motion. Replaced
   entirely with a scroll-pinned, 7-stage product walkthrough. See
   `CLAUDE.md` §9 for the complete architecture; summary: one tall
   (`h-[420vh]`) pinned section, `scrollYProgress` drives 7 explicit
   per-stage `useTransform` values plus one discrete `activeStage`
   React state (updated at most 6 times total via
   `useMotionValueEvent`), the whole story built on one real fixture
   finding moving through Persona-attempts → Ground → Propose-fix →
   Sandbox → Verify (only Aggregate pulls in other findings), with a
   non-pinned `whileInView`-based fallback below `lg` and whenever
   `prefers-reduced-motion` is set.
6. **ConcernCloud** — tags settle in with a small random per-tag
   rotation instead of a uniform grid stagger; a soft radial highlight
   fades in behind the stakeholder card before it does.
7. **CapabilityGrid** — **full rebuild as a sticky-scroll section.**
   One shared sticky panel (`sticky top-1/2 -translate-y-1/2`, true
   viewport center) crossfades through 4 pieces of content while 4 text
   blocks scroll past beside it. Went through several structurally
   different attempts (see "Status as of this revision" above and
   `CLAUDE.md` §§6, 8 for the full bug history) before landing on the
   current, verified-correct version: sticky child as a direct child of
   its `relative` containing block (no wrapper divs — a real Chromium
   bug otherwise), fixed-`px` block heights (not `vh`, which scaled
   dead space up on taller windows), and a mathematically-derived
   engage/release geometry verified pixel-exact via Playwright.
8. **FinalCta** — kept M6b's scale-up arrival as-is (already deliberate).
9. **Footer** — closing wordmark now clip-path reveals ("resolves" into
   view) after the three brand-mark dots finish popping in.

**On verifying this without eyeballing alone:** `tsc --noEmit` clean and
build succeeding confirm the code is correct; they don't confirm the
page *looks* right. This milestone's actual verification came from a
real look-and-iterate loop using a Playwright harness added this
session specifically for this purpose (screenshots plus direct
`getComputedStyle`/`getBoundingClientRect()` inspection at exact scroll
positions) — see `CLAUDE.md` §11 for the reusable pattern. Several real
bugs (not just polish) were only caught this way.

- **Verify:** `tsc --noEmit` clean; grep confirms `Trace.tsx` is not
  reintroduced; the capability section's `lg:` and sub-`lg:` layouts
  are both present; the `active` prop on the M5 persona components
  defaults compatibly with every existing call site.

## M7 — New-run / persona-selection screen ✅ Done

- Large, soft-radius (`card-chart-lg`) persona cards for all three
  personas, each stating its restriction in plain language (reusing
  `persona.restriction` from fixture data), with M5's "at-rest" metaphor
  thumbnail embedded (`AccessibilityRestrictedView size="thumbnail"`,
  `MotorImprecisePointer size="icon"`, exactly as `PersonaShowcase`
  does — mobile-first reuses the same dashed "preview" placeholder box,
  no new mobile-first simulation invented, since none is planned before
  FYP-II).
- Mobile-first card present, badged "Phase 2 · FYP-II" using the
  `--persona-phase2` grey tint — **never a persona color, and never
  dimmed/disabled.** This reverses the milestone's own original "mobile-
  first card is clearly inert/non-selectable" verify criterion below,
  consistent with the correction already noted for `PersonaShowcase`'s
  cards (see "Status as of this revision," item 2) and reinforced by
  explicit instruction this session ("start M7 but don't block the
  mobile-first persona").
- **Deliberate deviation from this plan's own literal text.** This
  milestone originally specified "Card selection built on Radix's
  accessible selection semantics (radio-group under the hood)" — i.e.
  single-select. Built instead with **`@radix-ui/react-toggle-group`,
  `type="multiple"`** (a new dependency, added this session) — a strict
  single-select radio-group contradicts the product's own concept:
  `PipelineStages`' own copy says "whichever personas you picked"
  (plural), and the Aggregate stage already combines findings from
  multiple personas in one run. Each card is independently selectable
  (`data-state="on"|"off"`, `aria-pressed`), which also makes "don't
  block mobile-first" trivial — it's just another toggleable card, not
  a special case to unblock.
- Selection state uses a ring (`ring-2 ring-ink ring-offset-2`) around
  the whole card plus a small black circular checkmark badge in the
  corner — explicitly not a checkbox square. Driven by Tailwind's
  `group-data-[state=on]:` variant reacting to Radix's own `data-state`
  attribute, not a separately-tracked `selected` boolean prop.
- "Continue" button is disabled with the label "Select at least one
  persona" until ≥1 card is selected, then becomes a real `Link` reading
  "Continue with N persona(s)." Deliberately built as two different
  elements (`<Button disabled>` vs. `<Button asChild><Link>`) rather
  than a `disabled` Button wrapping a `Link` — a `disabled` HTML
  attribute doesn't stop an anchor tag from navigating, so that
  combination would have been a real, easy-to-miss bug.
- Selection state stays local `useState` in `NewRun.tsx` — not wired
  into router state or any shared store, since nothing downstream
  (M8+) exists yet to consume it. `Running.tsx` was not touched.
- **Verify (updated from the original criteria):** keyboard Tab +
  Enter/Space selects a card (confirmed via Playwright — Tab reaches a
  persona card as a real focusable button, Enter toggles `data-state`
  to `on`); no checkbox/toggle appearance anywhere; **mobile-first card
  is genuinely selectable, not inert** (confirmed via Playwright —
  clicking it produces the exact same `data-state="on"` /
  `aria-pressed="true"` as the other two cards).

## M8 — Running / execution state (seven-stage animated walkthrough) ✅ Done

- `Running.tsx` rebuilt (no longer the M4 placeholder). Keeps the
  honesty principle — a real, ticking elapsed-time display (`0:07`,
  driven by an actual `Date.now()` delta), never a fake percentage —
  and walks the same seven named stages from `run.stages`.
- **Reused `PipelineStages.tsx`'s stage visuals directly rather than
  rebuilding seven cards a second time.** Exported its `StageVisual`
  component and generalized the three sub-components that were
  hardcoded to the accessibility persona/finding (`PersonaVisual`,
  `FixVisual`'s code-snippet chip, `VerifyVisual`'s summary line) so
  they branch on `persona.id`/`finding.id` instead — `PipelineStages`'
  own two call sites (desktop + `MobileStages` fallback) keep passing
  the accessibility persona/finding unchanged, so this was a pure
  generalization, not a behavior change to the landing page.
- **Wired "driven by whichever persona(s) were picked in M7"**: the
  Continue link on `NewRun.tsx` now passes `state={{ personaIds:
  selected }}` via React Router — the smallest mechanism that works,
  since nothing else in the app needs this value and its lifetime
  should be exactly "until this run finishes" (not a global store, not
  a query param). `Running.tsx` reads it via `useLocation().state` and
  picks whichever of accessibility/motor was selected (accessibility
  preferred if both were); falls back to accessibility if accessed
  directly with no state, or if only mobile-first was selected (it has
  no real showcase finding to narrate yet, per `POC_SPEC.md` §6 item 5).
- **`Trace.tsx` stale reference resolved** — built a fresh non-clinical
  spine instead: a light-mode `RunningIndicator` (numbered stages +
  a continuously-filling progress line driven by a `MotionValue`, not
  React state, so it doesn't re-render every 200ms tick) matching
  `PipelineStages`' own `PipelineIndicator` but in the page's light
  palette rather than that section's dark one.
- **Scripted, not simulated-live**: a fixed `STAGE_DURATIONS_MS` array
  (2.5–4s per stage, ~21.5s total) drives stage advancement via chained
  `setTimeout`s, not polling of any kind; auto-navigates to `/results`
  when the sequence completes. A "Skip to results →" link is also
  present for practical use (e.g. during a live defense) — a reasonable
  addition since skipping a known, fully-scripted sequence doesn't
  weaken any of the honesty guardrails.
- **Verify (all confirmed via Playwright):** stage labels appear in
  order (Crawl → ... → Aggregate) with correct timing; selecting only
  the motor persona on `NewRun.tsx` and continuing shows the motor
  persona's name and `MotorImprecisePointer`'s cursor animation during
  "Persona attempts," not the accessibility content; direct navigation
  to `/running` with no router state falls back to the accessibility
  persona; the elapsed timer genuinely increments across real wall-clock
  time; the "Skip to results" link and the full-duration auto-advance
  both correctly land on `/results`.

## M9 — Results / Aggregation dashboard ✅ Done

- `Results.tsx` rebuilt (no longer the bare-list M4 placeholder — no
  separate `ResultsView.tsx`/`ScorePanel.tsx` files were created; kept
  to this project's established one-file-per-page convention instead).
  Findings stay grouped by severity always; persona is a filter
  narrowing within that structure, not a replacement for it — matches
  "persona filter toggling changes visible cards while severity
  grouping stays intact" exactly (confirmed via Playwright: filtering
  to Motor shows exactly its 3 findings across the High/Medium/Low
  groups its findings actually fall in).
- **Deliberate scope decision**: results show the FULL fixture run
  regardless of which personas were picked in M7/M8 — that selection
  drove M8's own narration, not what data this dashboard displays.
  `run.findings`/`run.uiScore`/`run.history` are one fixed completed
  run in the fixture data; persona here filters that fixed report
  rather than restricting it to "only what was actually run." No new
  router-state hand-off was added for this reason.
- Persona filter options are derived from which personas actually have
  findings (`run.personas.filter(p => run.findings.some(...))`) —
  mobile-first is correctly never offered as a filter, since selecting
  it would always empty the list (POC_SPEC.md §4: placeholder only).
- Hero UI Score: large serif numeral via `CountUp`, with Visual Design
  and Accessibility-Visual demoted to an animated secondary breakdown
  row (bars fill via `motion`, not a fake computed transition).
- Run history: a bar chart across `run.history` + the current run,
  most-recent (current) run visually emphasized (solid ink vs. muted
  bars for prior runs), each bar's height driven by its own UI score —
  confirmed visually ascending (44→52→61→71) telling an honest
  improving-over-time story, matching the fixture data's own intent.
- Persona badges on finding cards use the same tint tokens as
  `PersonaShowcase`/`NewRun` (`persona-accessibility`/`persona-motor`)
  — no new color introduced.
- **Verify (confirmed via Playwright):** persona filter toggling
  changes visible cards while severity grouping stays intact; hero
  score count-up plays; history section shows all 3 prior runs plus
  the current one with a clear visual comparison; **zero non-font
  network requests** (only Google Fonts load, which is not a backend/
  computation call and has been used throughout this project since M0).

## M10 — Finding detail: fix → sandbox → verify showcase (×2) ✅ Done

- `FindingDetail.tsx` rebuilt (no longer the M4 placeholder). The two
  showcase findings (accessibility, motor/age — both already had full
  `showcase: { proposedFix, sandboxNote, verifyResult }` data in
  `fixtures/demoRun.ts`) get an interactive 3-step wizard: Propose fix
  → Sandbox → Verify, ending in M5's `VerifyStamp` pass/fail badge.
- **Reused `FixVisual`/`SandboxVisual`/`VerifyVisual` directly from
  `PipelineStages.tsx`** (exported alongside `StageVisual` for exactly
  this) rather than rebuilding the same three panels a third time — the
  landing-page preview (M6c), the Running-screen narration (M8), and
  this actual click-through walkthrough all show the same visual
  language for the same three steps.
- Every other finding (5 of the 7 in fixture data) renders as a plain
  recap — severity, persona badge, observation, recommendation, and its
  real citation if it has one — with an explicit, honest note that
  there's no walkthrough for it, rather than a silently thinner version
  of the showcase UI or a broken-looking empty state.
- Walkthrough advances only on user action (Next/Back buttons,
  `useState` step index) — never auto-plays. On the final step, "Next"
  becomes "Back to results" rather than looping or dead-ending.
- **Verify (confirmed via Playwright):** opening either showcase finding
  plays Propose fix → Sandbox → Verify on deliberate user advance,
  correctly ending in the stamp; Back navigation correctly steps
  backward; opening any other finding shows only the plain recap (no
  walkthrough controls at all) plus its real citation when present; an
  unknown finding id shows an honest "Not found" state instead of
  crashing or showing stale/wrong content.

## M11 — Correction/Learning panel (deliberately unfinished) ✅ Done

- `Correction.tsx` rebuilt (no longer the M4 placeholder) as a single
  plain panel: a paraphrase of the proposal's own §2.2.5 description
  (one sentence) plus a small static ASCII diagram (`Fix-verify
  outcome`/`Operator correction` → `Case store` → `New judgment`) in a
  `<pre>` block, both explicitly labeled "Planned for FYP-II." No
  `motion` import, no `useDemoRun()` fixture data, no interactivity —
  not an oversight, the correct amount of effort for this module.
- Deliberately skips the big `font-hero`/`text-d1` heading treatment
  every other screen uses — a plain `font-display text-3xl` heading
  instead, and `.label-mono` (the more utilitarian label style) rather
  than `.eyebrow-sans` (the more "designed" one used elsewhere) — small,
  intentional signals that this screen got less design attention,
  consistent with the honest-maturity-gradient rule.
- **Bug caught and fixed before calling this done**: the first version's
  diagram text overflowed its container and got visibly clipped
  ("judgments" cut mid-word) — confirmed via a real screenshot, not
  assumed. That's a genuine layout bug, not "intentionally minimal";
  fixed by shortening the diagram's labels and widening the panel
  slightly (`max-w-md` → `max-w-lg`), re-verified with a second
  screenshot showing it fits with room to spare.
- **Verify:** side-by-side against every other screen, this one reads
  as obviously thinner (no motion, no color, no persona tints, no hero
  serif) without looking broken — confirmed visually.

## M12 — End-to-end rehearsal and risk-guardrail audit ✅ Done

Executed against a **fresh production build** (`npm run build` +
`vite preview`, port 4173) — not the dev server — per the milestone's
own requirement. One genuine gap was found and fixed during the audit
(item 5); everything else passed as originally built.

### Pass/fail checklist

| # | Item | Result |
|---|---|---|
| 1 | Grep for `"Site Doctor"`/`"site-doctor"`/`AuditForm`/`AuditHistory`/`ErrorState`/"pick checks to run" | **PASS** — every hit (19 across `App.tsx`, `index.css`, `BrandMark.tsx`, `SectionHeading.tsx`, `Footer.tsx`, `SeverityTag.tsx`, `SiteNav.tsx`, `button.tsx`, `PersonaShowcase.tsx`, `NewRun.tsx`, `types.ts`) is inside a comment explaining what was ported/renamed/excluded — confirmed via a second grep excluding comment-prefixed lines, zero real hits. |
| 2 | Zero network requests across all six screens | **PASS** — tested all 6 routes plus a finding-detail page against the production build; 83 total requests, all either same-origin or Google Fonts, **zero** non-font third-party requests. |
| 3 | Re-verify every citation character-for-character against its live source | **PASS** — all three (`WCAG_4_1_2`, `WCAG_2_5_8`, `NIELSEN_VISIBILITY_OF_SYSTEM_STATUS`) re-fetched from their live URLs this session (not trusted from the M3 comment) and confirmed exact-match, including the WCAG-2.2-not-2.1 detail for SC 2.5.8. |
| 4 | Correction/Learning still visibly the least-polished screen | **PASS** — comparative grep across all six pages: `Correction.tsx` has 0 `motion`/`AnimatePresence` references and 0 `font-hero` references (every other page has 1-10); its one `useDemoRun` grep hit is inside a comment explaining the deliberate absence, not an actual import. |
| 5 | Re-read every in-app string against "never imply live execution" | **PASS, with one gap found and fixed** — grepped for risky phrasing (detecting/analyzing/scanning/computing/"in progress"/etc.): zero hits. But `FindingDetail.tsx`'s fix→sandbox→verify wizard — exactly the screen `POC_SPEC.md` §7 names as this risk's specific danger point — had no explicit honesty disclaimer, unlike `Running.tsx`/`Results.tsx`/`PipelineStages.tsx`, which all do. Added: *"A scripted walkthrough, advanced by you — not a live fix applied and re-verified in real time."* directly above the wizard panel. |
| 6 | Mobile-first Phase-2-badged everywhere, no showcase | **PASS** — zero `findings` entries with `personaId: "mobile-first"`; the `Phase 2 · FYP-II` badge is gated identically (`persona.depth === "placeholder"`) in both `PersonaShowcase.tsx` and `NewRun.tsx`, the only two places it's rendered as a card. |
| 7 | Dev-only routes excluded from the production build | **PASS** — confirmed at two levels: (a) zero occurrences of `dev/tokens`/`dev/fixture`/`dev/metaphors` or any dev-page-specific content anywhere in the built JS bundle (Vite's `import.meta.env.DEV` is statically `false` in production, so Rollup dead-code-eliminates the routes AND their component code entirely, not just hides them); (b) confirmed at runtime against the actual served production build — hitting `/dev/tokens` etc. correctly falls through to the app's own catch-all (renders Landing), not a 404 or stale dev content. |

**Verify (the milestone's own criterion):** the table above is exactly
that pass/fail checklist, one line per item, walked against the running
production build via Playwright rather than the dev server — satisfies
"not just dev." No items are failing; one was fixed in place during the
audit rather than deferred.

---

## Critical files (existing, ported from / referenced against)

- `POC_SPEC.md`, `DESIGN.md` — governing specs
- `site-doctor/frontend/src/index.css`, `tailwind.config.js` — original token source (M1)
- `site-doctor/frontend/src/lib/motion.ts`, `lib/utils.ts`, `lib/stock.ts` — original motion/util source (M2)
- `site-doctor/frontend/src/components/{SeverityTag,CountUp,SectionHeading,SiteNav,Footer}.tsx`
  (`Trace.tsx` was ported in M2 then deleted post-M4 with the rest of
  the clinical-instrument metaphor — do not re-port it)
- `site-doctor/frontend/src/components/app/{RunningState,ResultsView,ScorePanel,IssueCard,UxSuggestionCard}.tsx`
  — reference for M8-M10's still-unbuilt screens
- `site-doctor/frontend/src/components/ui/*.tsx`
- `site-doctor/frontend/package.json`, `vite.config.ts`, `tsconfig*.json`, `index.html`, `components.json`

## Explicitly not ported

`AuditForm.tsx` (checkbox-list mental model), `lib/api.ts` (real HTTP
client), `AuditHistory.tsx`'s Supabase logic, `ErrorState.tsx`'s backend
checklist, any SEO/security code, any Site Doctor branding/copy, the
screenshot-plus-roleplay-prompt UX-review framing.
