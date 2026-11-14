# CLAUDE.md — SimUX web interface

> **Update, 14 Nov 2026 (moved into `Sim-UX/web/`).** This app now lives in
> the main repository and is no longer fully static. New Run (`/new-run`)
> calls the real API (`api/`, see `src/lib/api.ts`) and opens
> `/runs/:runId` (`pages/LiveRun.tsx`), which streams a real run's steps and
> shows its grounded findings through `hooks/useRun.ts`. Set
> `VITE_SIMUX_API_URL` (see `.env.example`); local development expects
> `uvicorn api.app:app --port 8000` from the repo root. The landing page,
> `/running`, `/results`, `/results/:id` and `/correction` still read the
> fixture through `useDemoRun()` and keep their "scripted" labels; they move
> to the real API and the three spec personas (Error-prone, Memoryless,
> Low-literacy) in Sprint 2. Rule 1 below ("nothing executes") now holds
> only for those fixture screens. The repository-wide rules are in the root
> `CLAUDE.md`.

## Original POC context

This file is a complete handoff document for the **SimUX POC** — paste it
into a new chat (along with `DESIGN.md` and `POC_SPEC.md`) if you need to
continue work with a different Claude session. It captures the
architecture, the decisions behind it, what's actually built vs. stubbed,
and every non-obvious bug/gotcha already hit and fixed, so you don't have
to rediscover them.

---

## 1. What this project is

**SimUX** is a Final Year Project: a multi-persona LLM-agent UI/UX
auditor built around six modules (Agent, Execution, Remediation,
Grounding, Correction/Learning, Aggregation) that will eventually crawl
a real website, drive genuinely *restricted* synthetic personas through
real tasks, detect friction, ground findings in real WCAG/Nielsen
sources, propose and sandbox-verify fixes, and aggregate everything into
a ranked report. None of that pipeline exists as working software yet —
see `SimUX_FYP_Proposal-2.pdf` for the full target system and its
two-semester (FYP-I/FYP-II) timeline.

**This repository (`simux-poc/`) is NOT that system.** It is a
**100% static, fully click-through visual prototype** built for the
FYP-I defense presentation, whose ask is "show us what you're going to
build," not "prove it works." The full governing spec is
`POC_SPEC.md` — read it before changing scope or content, but the rules
that matter most day-to-day:

1. **Nothing executes.** No agent runs, no LLM is called, no browser is
   launched, no real computation happens anywhere in this app, ever.
2. **Dummy data throughout**, EXCEPT citations — every WCAG/Nielsen
   citation string shown on screen must be genuine, verbatim, hand-
   verified text (see `src/lib/fixtures/citations.ts`). Fabricating a
   citation inside a demo of an anti-hallucination feature would be a
   uniquely bad failure mode if caught.
3. **One fixture-data seam** (`useDemoRun()`) is the only place screens
   read data from — built so a real backend can later replace just that
   one hook's implementation.
4. **Honest maturity gradient** — Detection/Grounding/the fix-verify
   showcase get full polish; Correction/Learning is deliberately the
   least-polished screen in the app, not faked at the same fidelity.
5. Mobile-first persona is explicitly a **Phase 2 / FYP-II placeholder**
   in the fixture data and UI copy — but as of M7 (see §10) it is NOT
   visually or interactively disabled. It's badged, not blocked.

**This is a separate project from `site-doctor/`.** Site Doctor is an
earlier, broader auditing tool (SEO+UX+Security) that predates SimUX and
lives in a sibling directory. Only specific, explicitly-identified
pieces are ever ported from it into `simux-poc/` (its React frontend
skeleton, `lib/motion.ts`, a handful of `ui/*` primitives) — SimUX code
and docs belong here, in `simux-poc/`, never in `site-doctor/`.

---

## 2. Tech stack

| Layer | Tool | Notes |
|---|---|---|
| Framework | Vite 6 + React 18 + TypeScript 5.7 | `npm run build` = `tsc -b && vite build`; `npm run lint` = `tsc --noEmit` (no separate ESLint config in this project) |
| Styling | Tailwind CSS 3.4 + `tailwindcss-animate` | All design tokens are CSS custom properties in `src/index.css`, consumed via `tailwind.config.js` |
| Animation | `motion` (Framer Motion's `motion/react` package), v12 | The **only** animation library in this project — deliberately. No GSAP. `useScroll`/`useTransform`/`useMotionValueEvent` handle all scroll-scrubbed/pinned work; see §11. |
| Routing | `react-router-dom` v6 | Six top-level routes, see §3 |
| Accessible primitives | Radix UI (`react-checkbox`, `react-collapsible`, `react-label`, `react-separator`, `react-slot`, `react-switch`, `react-toggle-group`) | Wrapped in `src/components/ui/*` following the shadcn-style `forwardRef` + `cn()` pattern, but hand-written, not shadcn-generated |
| Icons | `lucide-react` | |
| Class utilities | `class-variance-authority`, `clsx`, `tailwind-merge` (via `cn()` in `lib/utils.ts`) | |
| Browser testing | `playwright` (added as a **devDependency** this session) | Not part of the app — used to actually verify scroll/sticky/layout behavior instead of reasoning about it blind. See §11. |
| Fonts | Google Fonts, loaded via `<link>` in `index.html` | Bricolage Grotesque, Instrument Serif (`ital@0;1`), Source Serif 4, IBM Plex Mono |

No backend, no database, no API calls anywhere in the runtime app —
by design (rule 1, §1).

---

## 3. Repository structure

```
simux-poc/
    src/
        App.tsx                    <- Router + ScrollBehaviour (hash/top-of-page
                                       scroll-restore on navigation — see §12
                                       "not a bug" entry if a page load seems to
                                       jump to a section on its own)
        main.tsx
        index.css                   <- ALL design tokens (see DESIGN.md)
        pages/
            Landing.tsx              <- Fully built (M0-M6c, see §10)
            NewRun.tsx               <- M7, DONE — real multi-select persona-selection screen, see §10
            Running.tsx              <- M8, DONE — scripted 7-stage walkthrough, see §10
            Results.tsx              <- M9, DONE — severity/persona-filtered dashboard, see §10
            FindingDetail.tsx        <- M10, DONE — fix->sandbox->verify wizard (×2 showcases), see §10
            Correction.tsx           <- M11, DONE — deliberately plain, see §10
            dev/
                Tokens.tsx, Fixture.tsx, Metaphors.tsx
                                     <- Dev-only routes (import.meta.env.DEV
                                        guarded in App.tsx), never linked from
                                        nav/footer. Must be confirmed gone or
                                        still gated at the M12 audit.
        components/
            SiteNav.tsx              <- Floating full-bar -> pill nav, scroll-driven
            Footer.tsx
            BrandMark.tsx            <- Three-dot mark (one per persona) + wordmark
            SectionHeading.tsx       <- Shared eyebrow+rule+word-reveal-title+lede
            SeverityTag.tsx          <- High/Medium/Low tag, fill or outline variant
            VerifyStamp.tsx          <- Hard-shadow pass/fail "stamp" badge
            CountUp.tsx              <- Generic number-settle animation
            landing/
                Hero.tsx             <- Real Normal/Accessibility-view toggle
                GroundedInStandards.tsx
                PersonaShowcase.tsx  <- The 3 persona cards shown on the landing page
                                        (NOT the same as NewRun.tsx's selection
                                        cards — this is a marketing showcase,
                                        M7's cards are a real selection control)
                Comparison.tsx
                PipelineStages.tsx   <- "How it works" — scroll-pinned 7-stage
                                        walkthrough. Fully rebuilt this session,
                                        see §9.
                ConcernCloud.tsx
                CapabilityGrid.tsx   <- "Four things every report has" — sticky-
                                        panel scroll section. Extensively fixed
                                        this session, see §8.
                FinalCta.tsx
            personas/
                AccessibilityRestrictedView.tsx  <- The blur+linearized-list metaphor
                MotorImprecisePointer.tsx         <- The miss-then-correct cursor metaphor
                PageMockup.tsx                     <- Marlow's checkout page, built from
                                                       real markup, deliberately embodies
                                                       three real fixture findings
            ui/
                button.tsx, checkbox.tsx, collapsible.tsx, input.tsx, label.tsx,
                separator.tsx, skeleton.tsx, switch.tsx
                toggle-group.tsx     <- Added M7, backs NewRun.tsx's multi-select cards
        hooks/
            useDemoRun.ts            <- THE fixture-data seam (see §1 rule 3)
            useActiveSection.ts      <- useSectionInView(index, onActive) — IntersectionObserver-based "which block is centered" tracker, used by CapabilityGrid
        lib/
            types.ts                 <- All fixture data types (Persona, Finding, Citation, DemoRun, etc.)
            motion.ts                 <- Shared easing/variants/useParallax (see §7)
            utils.ts                  <- cn()
            fixtures/
                demoRun.ts            <- THE dummy data: product "Marlow", 2 tasks
                                         (signup, checkout), 7 pipeline stages, 7
                                         findings, UI score, run history
                citations.ts          <- 3 real, hand-verified WCAG/Nielsen citations
    POC_SPEC.md                      <- Governing spec — read before changing scope
    DESIGN.md                        <- Visual design system reference (this session:
                                         rewritten to describe the CURRENT implemented
                                         system, not the original Wispr research memo)
    CLAUDE.md                        <- This file
```

---

## 4. Key design decisions and their rationale

- **Fixture-data seam, one hook.** `useDemoRun()` is the *only* function
  any screen reads data through. Swapping in a real backend later means
  changing that one hook's implementation, never the screens. Never
  import `lib/fixtures/demoRun.ts` directly from a component.
- **Real content over generic placeholders, everywhere possible.**
  `PageMockup` isn't an arbitrary mockup — it's built from real markup
  that deliberately embodies three specific fixture findings (a
  ~18px "Apply" button, a stepper whose minus button sits too close to
  the input, an icon-only "Continue" button with no accessible name).
  `PipelineStages`' entire 7-stage walkthrough is built around ONE real
  finding (`a11y-checkout-continue-button`) moving through the whole
  pipeline, not seven unrelated illustrations — see §9.
- **Persona restriction is a genuine constraint, never a roleplay
  instruction** — this is the project's actual novelty claim (per the
  proposal's own literature review) and the POC exists specifically to
  *show* that, not just say it. `AccessibilityRestrictedView` renders a
  blurred/desaturated screenshot beside a plain linearized reading-order
  list — a literal visual metaphor for "this agent cannot see the
  screenshot, only this list." `MotorImprecisePointer` animates a cursor
  that misses a small target before correcting. Both are real,
  reusable components, not one-off decoration.
- **Two-tier severity/persona color separation, never mixed.** Severity
  colors (`critical`/`caution`/`minor`) are functional and must stay
  legible/consistent; persona tints (`persona-accessibility`/`-motor`/
  `-phase2`) are chosen to sit outside those hues specifically so a
  persona-colored card is never mistakable for a severity signal. Never
  apply both tinting systems to the same card.
- **Dropped Site Doctor's "clinical instrument" visual identity
  entirely** — the graph-paper grid background and the ECG/vitals-trace
  motif (`Trace.tsx`) were deleted, not hidden, along with ported code
  that referenced them. `BrandMark`'s icon is three dots (one per
  persona), not a heartbeat line. If you see a stale reference to
  `Trace.tsx` in an old plan document, it's dead — do not resurrect it.
- **`motion/react` only, no second animation library.** Every scroll-
  driven, pinned, or scrubbed interaction in this codebase — including
  the two hardest ones (`CapabilityGrid`, `PipelineStages`) — is built
  with `useScroll`/`useTransform`/`useMotionValueEvent`, not GSAP. This
  was a deliberate choice made when building `PipelineStages`: GSAP was
  the "preferred" tool per one set of instructions, but the project
  already had a fully capable scroll-scrub library in active use, and
  adding a second one for the same job would have been unjustified.
- **No global "which personas are selected" state (yet).** M7's
  selection screen (in progress) keeps selection as local component
  state — nothing downstream (M8-M11) is built yet to consume it, so
  wiring up shared/persisted state now would be speculative. Revisit
  this once M8 actually needs to know what was selected.

---

## 5. Design tokens — see DESIGN.md for the full reference

`DESIGN.md` is the authoritative, current design-system doc (colors,
type scale, radius/shadow tiers, motion primitives, the persona visual
language, the sticky-scroll patterns). This file won't duplicate it —
read it before styling anything. The one-paragraph summary: warm cream
paper background (`hsl(60 100% 96%)`, i.e. RGB 255,255,237), near-black
ink text, Bricolage Grotesque for UI/display headings, Instrument Serif
reserved for hero-scale headlines only, Source Serif 4 for body copy,
two-tier border radius (tight for UI elements, soft 24-40px for section-
level containers), thin hairline borders over shadows, no gradients, no
neon, no glassmorphism, no bounce/spring easing except a small number of
deliberate, explicitly-scoped exceptions (a few `type: "spring"`
transitions used for genuine "pop" moments — the footer dots, the
CapabilityGrid panel's own crossfade).

---

## 6. Known bugs already hit and fixed (don't reintroduce these)

| Bug | Fix |
|---|---|
| **`position: sticky` silently stops sticking when there's ANY plain, non-positioned `<div>` between the sticky element and its positioned (`relative`/etc.) containing-block ancestor.** Verified via an isolated, non-React, non-Tailwind repro in this exact Chromium build (Playwright's bundled Chromium, v151.0.7922.34) — the element still reports `position: sticky` and a correct `top`/`transform` via `getComputedStyle`, but behaves as pure static flow (moves 1:1 with scroll forever, never locks). Reproduced with padding-top, margin-top, AND a completely bare unstyled wrapper — all broke it equally; only removing the intermediate div (or moving any needed offset onto the containing block itself, e.g. as `padding` directly on the `relative` element) fixed it. | **Always make the sticky element a DIRECT child of its positioned containing-block ancestor.** If you need an offset/buffer before the sticky element's static position, apply it as padding/margin ON the containing block itself, never on a separate wrapper div in between. This bit `CapabilityGrid.tsx` (a `pt-[55vh]` buffer div silently broke the panel) — fixed by moving that padding onto `.relative` itself. |
| **`vh`-based heights on content-driven blocks make dead space WORSE the taller the browser window is**, not just "somewhat too spacious." `CapabilityGrid`'s four text blocks were `min-h-[45vh]` — at 900px viewport that's 405px per block against ~150px of actual text, but on a taller window (confirmed via a real user screenshot) the gap grows proportionally while the text stays the same size, producing very large dead zones. | Use a **fixed px** `min-h` for anything sized around fixed-size text/content, not `vh`. Changed to `min-h-[320px]` (`580px` for the block needing the sticky-panel release-timing compensation, see next entry) — verified visually identical at both 900px and 1000px viewport heights afterward. |
| **CSS sticky's release condition is NOT symmetric with its engage condition.** Engaging (`top: 50%`) only checks the element's own top edge crossing the threshold — no dependency on the element's height. Releasing DOES subtract the element's own height from how far it can travel. Naively expecting "panel center = first block's top" (engage) and "panel center = last block's bottom" (release) to both fall out of the same offset is wrong — the release will always land `panel height` short of the true last-block bottom unless compensated. | Derived the exact fix mathematically (not by trial and error) and verified it with a Playwright probe reading real `getBoundingClientRect()` values at the transition instant: give the LAST block exactly `+panel height` of extra `min-h` (nothing else needs the compensation). Confirmed pixel-perfect (`panelCenter === trueLastBlockBottom` at the exact release frame) both times this was needed. |
| **`AnimatePresence` with no explicit mode is fine; `mode="wait"` on a scroll-crossfade is not.** `mode="wait"` waits for the exit animation to finish before mounting the next child — on a fast scroll this reads as "the content disappears for too long." | Removed `mode="wait"` wherever a scroll-driven crossfade needs to track continuously (default sync mode crossfades old/new simultaneously, no gap). |
| **Reusing a component variant outside the width it was designed for silently overlaps other content instead of erroring.** `AccessibilityRestrictedView`'s `"full"` variant needs ~500px+ (a fixed 280px `PageMockup` + a readable list column in a 2-column grid) — used inside `PipelineStages`' ~460px-max column, its list wrapped so aggressively the whole block grew far taller than expected and spilled upward into unrelated content above it during the stage crossfade. | Don't force a reuse into a width it wasn't built for. Exported the underlying `READING_ORDER` array from `AccessibilityRestrictedView.tsx` and built a single-column stack (its own `"thumbnail"` variant + the list below, not beside) purpose-fit for the narrower context, instead of fighting the `"full"` variant's grid. |
| **A translucent/light-colored overlay border on top of a LIGHT card is invisible, even though `getComputedStyle` confirms it's rendering correctly with the "right" opacity.** `PipelineStages`' Crawl-stage structure outlines used `border-paper/60` (a light cream, meant for the dark section chrome around them) drawn directly over `PageMockup`, which has a light `bg-paper-raised` card background. Found via direct `getComputedStyle` inspection (opacity, border-style, border-color all "correct") after a screenshot showed nothing — the bug was color choice, not any of the properties that looked broken. | Match the overlay's color to what it's actually drawn ON (`border-ink/45`, `text-ink-3` — dark tones, since these sit on the light mockup), not to the ambient section palette around it. |
| **A stale `#hash` in the browser's address bar makes the site look like it "jumps to a random section on load."** Not a bug — `App.tsx`'s `ScrollBehaviour` deliberately `scrollIntoView`s whatever the URL hash points to on mount, so a leftover `#personas` (e.g. from clicking a nav link earlier in the session) reproduces exactly on the next reload. Confirmed via Playwright: bare URL → `scrollY: 0`; `#personas` URL → `scrollY: 934`, landing on Personas every time. | Not a fix — navigate to the bare URL (no hash) if this happens. Only change `ScrollBehaviour` if the actual desired behavior is "always start at top regardless of URL," which is a deliberate behavior change, not a bug fix. |
| **`useScroll({ target, offset: ["start start", "end end"] })` reaches `scrollYProgress === 1` BEFORE you've scrolled the section's full height** — specifically, one viewport-height early (`sectionHeight - viewportHeight` of scroll, not the full `sectionHeight`). This is correct, documented Framer Motion behavior (it's exactly the span during which the section is actually pinned), but it's surprising if you assume progress maps linearly across the section's full CSS height. In `PipelineStages` this shows up as the final "Aggregate" stage holding steady for roughly one extra viewport-height of scroll before the section releases. | Not a bug — a natural "dwell" on the final state before the pin releases, which reads as an intentional resting beat on the payoff rather than a stall. If it ever needs to be tighter, reduce the section's total height (`h-[420vh]`), not the offset config. |

---

## 7. Motion system reference (`src/lib/motion.ts`)

- `EASE = [0.16, 1, 0.3, 1]` — the one non-bounce curve used almost
  everywhere. "A machine part settling into place," per its own comment
  — decelerates hard, never overshoots.
- `transition(duration, delay)` — wraps `EASE` for one-off use.
- `containerVariants` / `containerVariantsSlow` — stagger-children
  parents (0.09s / 0.14s stagger respectively).
- `itemVariants` (rise), `fadeVariants` (arrive in place), `ruleVariants`
  (self-drawing hairline, `scaleX: 0 -> 1`), `revealVariants` (card-
  sized: rise + scale + slight `rotateX` tilt + blur-in, pair with a
  `perspective` on the parent), `revealFlatVariants` (same, no tilt),
  `wordVariants`/`wordContainerVariants` (per-word headline reveal, used
  by `SectionHeading`).
- `useParallax(target, distance)` — drifts an element against scroll
  while it crosses the viewport; respects `prefers-reduced-motion`
  (returns `undefined`, i.e. no transform, when reduced motion is on).
- **Deliberate exceptions to the no-bounce rule**: a handful of
  `type: "spring"` transitions exist on purpose (Footer's popping dots,
  `CapabilityGrid`'s panel crossfade) — these are explicitly-chosen
  "pop" moments, not drift from the system. Don't "fix" them to use
  `EASE` without checking why they're spring first.

---

## 8. `CapabilityGrid.tsx` — sticky-panel section, hard-won state

"Four things every report actually has." One shared sticky panel
(`sticky top-1/2 -translate-y-1/2`, true viewport center) crossfades
through 4 pieces of content while 4 corresponding text blocks scroll
past beside it. Went through several structurally different attempts
before landing on the current one — full history is in the file's own
top-of-component comment (worth reading before touching this file
again), but the two load-bearing facts:

1. The sticky div must be a **direct child** of the `.relative`
   containing block — no wrapper divs (§6, bug #1).
2. The panel's **center precisely reaches the first block's top** the
   moment it locks (needs zero extra top padding — this falls out of
   the engage-condition math for free) and **precisely reaches the last
   block's bottom** the moment it releases (needs the last block's
   `min-h` extended by exactly one panel-height — §6, bug #3). Both
   verified pixel-exact via Playwright, not eyeballed.

`useActiveSection.ts`'s `useSectionInView` hook drives which block is
"active" (full opacity, matching panel content) via a centered
IntersectionObserver `margin` band — this band's exact value has to
stay conceptually in sync with wherever the panel actually locks; the
file's own comment cross-references this.

---

## 9. `PipelineStages.tsx` — "How it works," full rebuild this session

Replaced a static 7-card grid entirely with a scroll-pinned product
walkthrough — the section behaves like a "watch SimUX run" demo, not a
list of steps. Structure:

- One tall (`h-[420vh]`) `relative` section, one `sticky top-0 h-screen`
  child (direct-child rule from §6 applies here too).
- `scrollYProgress` (0-1 across the pinned duration) drives 7 explicit
  `useTransform` calls (`p0`...`p6`, NOT a `.map()` loop — same
  rules-of-hooks discipline as `CapabilityGrid`'s explicit
  `useSectionInView` calls), each live only within its own 1/7 slice of
  scroll.
- `activeStage` (0-6) is the ONLY actual React state driven by scroll,
  updated via `useMotionValueEvent` — at most 6 times across the whole
  scroll range. Everything continuous (the Crawl stage's staggered
  outline reveal) runs on MotionValues via `useTransform`, which never
  trigger a React re-render.
- Each stage is a scroll-controlled **scene**, not a literal per-pixel
  scrub of every visual detail (e.g. cursor positions aren't tracked
  frame-by-frame) — a deliberate simplification that keeps the
  implementation legible and performant while still fully satisfying
  "scroll down advances it, scroll up reverses it, nothing plays on its
  own" (reversal is inherent to being driven by `scrollYProgress`, not
  separately implemented).
- **The whole story is built on ONE real fixture finding**
  (`a11y-checkout-continue-button` — accessibility persona, WCAG 2.2 SC
  4.1.2, already had a full `proposedFix`/`sandboxNote`/`verifyResult`
  in `fixtures/demoRun.ts`) moving through Persona attempts -> Ground ->
  Propose fix -> Sandbox -> Verify. Only the final Aggregate stage pulls
  in other findings, because aggregation is the one place multiple
  findings actually converge.
- **Fallback path**: below `lg`, AND whenever `prefers-reduced-motion`
  is set (at any width), the entire pinned/scrubbed experience is
  replaced by `MobileStages` — a plain stacked sequence using ordinary
  `whileInView` reveals, reusing the exact same per-stage visual
  components (`StageVisual`) so content can never drift between the two
  paths. A pinned scroll-jacked section is exactly the kind of motion a
  reduced-motion user is opting out of, and is also a known-bad pattern
  on small viewports (address-bar collapse, touch-scroll physics) — both
  cases share one fallback rather than two bespoke ones.

---

## 10. Milestone status (see the milestone plan for full per-item detail)

**Done:** M0 (scaffold) · M1 (tokens) · M2 (primitives) · M3 (fixtures/
citations) · M4 (routing shell — all 6 routes exist; every route now
has real content as of M11, see below) · M5 (persona-restriction +
verify-stamp visual spike) · M6/M6b (landing v1/v2) · M6c (landing
animation overhaul — `CapabilityGrid` and `PipelineStages` both fully
rebuilt and verified this session; see §§8-9) · **M7 (New-run /
persona-selection screen) · M8 (Running / execution-state walkthrough) ·
M9 (Results / Aggregation dashboard) · M10 (Finding detail
fix→sandbox→verify showcase) · M11 (Correction/Learning panel) · M12
(End-to-end rehearsal + risk-guardrail audit)** — all six built and
verified this session, see below. **The full six-screen POC (M0–M12) is
now complete — no milestone remains.**

**M7 — New-run / persona-selection screen — DONE.** `NewRun.tsx` is now
the real screen (no longer the M4 placeholder). `src/components/ui/
toggle-group.tsx` was added, wrapping the newly-installed
`@radix-ui/react-toggle-group` in the same `forwardRef` + `cn()` pattern
as `switch.tsx`/`checkbox.tsx`.

- **Deliberate deviation from the milestone plan's literal text**: the
  plan says "Radix's accessible selection semantics (radio-group under
  the hood)" — i.e. single-select. This session's instruction was
  explicit ("start M7 but don't block the mobile-first persona"), and
  on reflection a strict single-select radio-group contradicts the
  product's own concept: `PipelineStages`' own copy says "whichever
  personas you picked" (plural), and the Aggregate stage already
  combines findings from MULTIPLE personas in one run. **Built with
  `ToggleGroup type="multiple"`**, not a radio-group — each persona
  card is independently selectable (`data-state="on"|"off"`,
  `aria-pressed`), which also makes "don't block mobile-first" trivial
  — it's just another toggleable card, not a special case to unblock.
- Mobile-first: same visual/interactive polish as the other two cards
  (no dimming, no `disabled`), distinguished ONLY by the existing
  "Phase 2 · FYP-II" badge (`persona-phase2` tint) — this reverses the
  milestone plan's original "mobile-first card is clearly inert/non-
  selectable" verify criterion, consistent with a correction already
  noted in the plan's own "Status as of this revision" section (the
  same dimming was already removed from `PersonaShowcase`'s cards
  earlier). **Verified via Playwright**: clicking the mobile-first card
  produces `data-state="on"` / `aria-pressed="true"` exactly like the
  other two — genuinely selectable, not merely present.
- Metaphor thumbnails reuse `AccessibilityRestrictedView size="thumbnail"`
  and `MotorImprecisePointer size="icon"` exactly as `PersonaShowcase`
  does; mobile-first reuses `PersonaShowcase`'s existing dashed
  "preview" placeholder box rather than inventing a new visual — no
  dedicated mobile-first restriction simulation exists (or is planned
  before FYP-II) per the fixture data's own comments, so building one
  now would have been scope creep beyond "a selection screen."
- **Selection-state visual**: a ring (`ring-2 ring-ink ring-offset-2`)
  around the whole card plus a small black circular checkmark badge in
  the top-right corner — explicitly not a checkbox square. Driven
  entirely by Tailwind's `group-data-[state=on]:` variant reacting to
  Radix's own `data-state` attribute on the button — no separate
  `selected` boolean threaded down as a prop just for styling.
- **Continue button** is disabled with the label "Select at least one
  persona" until ≥1 card is selected, then becomes a real `Link` (via
  `asChild`) reading "Continue with N persona(s)" — the button's own
  label communicates the gating state, not just its disabled styling.
  Deliberately rendered as two different elements (`<Button disabled>`
  vs. `<Button asChild><Link>`) rather than one `disabled` Button
  wrapping a `Link` — a `disabled` attribute doesn't stop an anchor tag
  from navigating, so that combination would have been a real,
  easy-to-miss bug if built the "obvious" way.
- **Verified via Playwright**: Tab reaches a persona card as a real
  focusable button (not a decorative click target), Enter toggles
  `data-state` to `on` — confirms genuine keyboard operability, not
  just mouse-click support.
- Selection state was local `useState` in `NewRun.tsx` only, at the
  time M7 shipped — **M8 (below) added the hand-off to `Running.tsx`**,
  so this is no longer the full picture; see M8's entry.

**M8 — Running / execution-state walkthrough — DONE.** `Running.tsx` is
now the real screen (no longer the M4 placeholder).

- **Reused `PipelineStages.tsx`'s stage visuals instead of rebuilding
  seven cards a second time.** Exported its `StageVisual` component and
  generalized the three sub-components that were hardcoded to the
  accessibility persona/finding (`PersonaVisual`, `FixVisual`'s
  code-snippet chip via a new `FIX_SNIPPETS` lookup, `VerifyVisual`'s
  summary line — now just `finding.recommendation`) so they branch on
  `persona.id`/`finding.id`. `PipelineStages`' own two call sites
  (desktop scroll version + `MobileStages` fallback) still pass the
  accessibility persona/finding, unchanged — this was a pure
  generalization of already-shared code, not a landing-page behavior
  change.
- **Persona hand-off**: `NewRun.tsx`'s Continue `Link` now passes
  `state={{ personaIds: selected }}` via React Router. `Running.tsx`
  reads `useLocation().state` and picks accessibility if selected,
  else motor if selected, else falls back to accessibility (covers
  direct navigation with no state, and mobile-first-only selections,
  since mobile-first has no real showcase finding yet). Deliberately
  router `state`, not a global store or query param — nothing else in
  the app needs this value, and its lifetime should be exactly "until
  this run finishes."
- **`Trace.tsx` stale reference resolved** (flagged in the milestone
  plan as needing a fresh replacement) — built `RunningIndicator`, a
  light-mode stage spine (numbered stages + a continuously-filling
  progress line on a `MotionValue`, not React state) matching
  `PipelineStages`' own `PipelineIndicator` but in the page's light
  palette.
- **Scripted, not simulated-live**: a fixed `STAGE_DURATIONS_MS` array
  (~21.5s total) drives stage advancement via chained `setTimeout`s;
  auto-navigates to `/results` on completion. A real, ticking
  elapsed-time display (`Date.now()` delta, not a fake percentage) plus
  a "Skip to results" link for practical use.
- **Verified via Playwright**: stage labels advance in correct order
  with correct timing; selecting only the motor persona on `NewRun.tsx`
  and continuing shows the motor persona's name and
  `MotorImprecisePointer`'s animation during "Persona attempts," not
  accessibility's content; direct navigation to `/running` with no
  router state falls back to accessibility; the elapsed timer genuinely
  increments in real time; both the skip link and the full-duration
  auto-advance correctly land on `/results`.

**M9 — Results / Aggregation dashboard — DONE.** `Results.tsx` is now
the real dashboard (no longer the bare-list M4 placeholder).

- Findings stay grouped by severity always; a persona filter narrows
  within that structure rather than replacing it (built with the same
  `ui/toggle-group.tsx` primitive from M7, `type="single"` this time).
  **Verified via Playwright**: filtering to Motor shows exactly its 3
  findings, correctly distributed across whichever severity groups they
  actually fall in — severity grouping never collapses when a persona
  filter is applied.
- **Deliberate scope decision**: shows the full fixture run regardless
  of which personas were picked in M7/M8 — see the reasoning already
  recorded above (before M9 started) for why no new router-state
  hand-off was added for this.
- Persona filter options are derived from which personas actually have
  findings, so mobile-first is never offered as a filter (it would
  always empty the list).
- Hero UI Score via `CountUp`; Visual Design/Accessibility-Visual
  breakdown bars animate in via `motion`, not a fake computed value.
- Run history: a bar chart across `run.history` plus the current run,
  current run visually emphasized — confirmed ascending (44→52→61→71),
  an honest improving-over-time story matching the fixture data.
- **Verified via Playwright**: zero non-font network requests (only
  Google Fonts, already in use since M0 — not a backend/computation
  call); clicking a finding correctly routes to `/results/:findingId`.

**M10 — Finding detail: fix → sandbox → verify showcase (×2) — DONE.**
`FindingDetail.tsx` is now the real screen (no longer the M4
placeholder).

- The two showcase findings (accessibility, motor — `POC_SPEC.md` §6
  item 5) get an interactive 3-step wizard: Propose fix → Sandbox →
  Verify, ending in M5's `VerifyStamp`. **Reused `FixVisual`/
  `SandboxVisual`/`VerifyVisual` directly from `PipelineStages.tsx`**
  (exported alongside `StageVisual` for exactly this) rather than
  rebuilding the same three panels a third time — now three different
  places (landing preview, Running narration, this walkthrough) share
  one visual language for the same three steps.
- Every other finding renders as a plain recap (observation,
  recommendation, real citation if present) with an explicit, honest
  note that there's no walkthrough — not a silently thinner showcase UI.
- Advances only on user action (Next/Back); "Next" becomes "Back to
  results" on the final step rather than looping or dead-ending.
- **Verified via Playwright**: full Propose-fix → Sandbox → Verify
  progression plus backward navigation both work correctly; non-
  showcase findings show no walkthrough controls at all; an unknown
  finding id shows an honest "Not found" state.

**M11 — Correction/Learning panel — DONE.** `Correction.tsx` is now a
single plain panel (no longer the M4 placeholder) — deliberately the
least-polished screen, per §1 rule 4, not an oversight.

- One-sentence paraphrase of the proposal's §2.2.5 (Correction/Learning
  Layer) description, plus a small static ASCII diagram (`Fix-verify
  outcome`/`Operator correction` → `Case store` → `New judgment`) in a
  `<pre>` block, both labeled "Planned for FYP-II." **No** `motion`
  import, **no** `useDemoRun()` fixture data, **no** interactivity —
  correct for this module, not something to "finish" later.
- Deliberately skips the big `font-hero`/`text-d1` heading and
  `.eyebrow-sans` label every other screen uses, in favor of a plain
  `font-display text-3xl` heading and `.label-mono` — small, intentional
  signals of "less design attention here," not inconsistency.
- **Real bug caught via screenshot, not assumed away**: the first
  version's ASCII diagram overflowed its container and got visibly
  clipped ("judgments" cut mid-word). Fixed by shortening the diagram's
  labels and widening the panel slightly; re-verified with a second
  screenshot showing it fits with room to spare. "Deliberately minimal"
  and "actually broken" are different things — this session caught the
  difference rather than assuming a plain page can't have bugs.

**M12 — End-to-end rehearsal + risk-guardrail audit — DONE.** Executed
against a **fresh production build** (`npm run build` + `vite preview`,
port 4173), not the dev server — the milestone's own requirement, since
dev-only route exclusion and real bundle behavior can't be confirmed
against `npm run dev`.

- Full 7-item pass/fail checklist (branding grep, zero-network-request
  check across all six screens, citation re-verification via live
  WebFetch against the real W3C/NN-g sources, Correction/Learning still-
  least-polished comparative grep, risky-language grep, mobile-first
  badging consistency, dev-route production exclusion) — all 7 passed.
  Full table is in `MILESTONES.md`'s M12 section; not duplicated here.
- **One genuine gap was found and fixed, not just confirmed-clean**:
  grepping for risky live-execution language (detecting/analyzing/
  scanning/"in progress"/etc.) returned zero hits, but `POC_SPEC.md` §7
  names the fix→sandbox→verify wizard specifically as this risk's
  highest-danger screen, and checking that screen directly (not just
  trusting the grep) showed `FindingDetail.tsx`'s `Walkthrough` component
  had no honesty disclaimer, unlike `Running.tsx`/`Results.tsx`/
  `PipelineStages.tsx`, which all do. Fixed by adding one line directly
  above the wizard's dark panel: *"A scripted walkthrough, advanced by
  you — not a live fix applied and re-verified in real time."* Rebuilt
  and re-verified via Playwright that it renders correctly and the page
  still fires zero network requests.
- Dev-route exclusion confirmed at two levels, not just one: (a) zero
  occurrences of `dev/tokens`/`dev/fixture`/`dev/metaphors` anywhere in
  the built JS bundle (Vite's `import.meta.env.DEV` is statically
  `false` in production, so Rollup dead-code-eliminates the routes AND
  their component code, not just hides them at runtime); (b) hitting
  `/dev/tokens` etc. against the actual served production build
  correctly falls through to the app's own catch-all (renders Landing),
  confirmed live, not just inferred from the bundle grep.
- **Lesson worth keeping**: "grep for bad words returns zero hits" and
  "the specific named risk in the spec is actually covered" are
  different questions — this audit's only real finding came from
  checking the second one directly rather than trusting the first as
  sufficient.

**No milestone remains — M0 through M12 are all built, verified, and
documented.**

---

## 11. Browser verification workflow (established this session)

**Playwright is installed as a devDependency specifically for verifying
scroll/sticky/layout behavior directly, instead of reasoning about CSS
mechanics blind.** This proved essential — several of the bugs in §6
were only found this way (a screenshot alone didn't explain them; direct
`getComputedStyle`/`getBoundingClientRect()` inspection did). Chromium
itself doesn't need a separate install — it's already cached at
`~/Library/Caches/ms-playwright` from `site-doctor`'s Python Playwright
setup, and the Node package resolves to that same cache.

Pattern used repeatedly, worth reusing rather than reinventing:

```js
import { chromium } from "playwright";
const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
// Force deterministic scrollTo, no smooth-scroll interference —
// html has `scroll-behavior: smooth` globally (index.css), which
// makes window.scrollTo() ANIMATE and overlap with subsequent calls,
// producing chaotic non-monotonic scrollY readings if you don't do this.
await page.emulateMedia({ reducedMotion: "no-preference" }); // or "reduce" to test that fallback path
await page.goto("http://localhost:5173/", { waitUntil: "load" });
await page.evaluate((y) => window.scrollTo(0, y), someY);
await page.waitForTimeout(50-300); // let motion values / crossfades settle
// Then EITHER screenshot, OR (often more diagnostic) evaluate() to read
// getBoundingClientRect()/getComputedStyle() directly — screenshots alone
// missed both the sticky-wrapper bug and the invisible-outline-color bug.
```

Write throwaway probe scripts as `probe-*.mjs` in the project root (NOT
`scratchpad/`, since they need Node's module resolution to find the
locally-installed `playwright` package) and delete them when done — none
should be committed. `emulateMedia({ reducedMotion: "reduce" })` is also
how the reduced-motion fallback path gets tested, since it flips the
same `prefers-reduced-motion` media query the app itself checks.

---

## 12. User context (for tone/pacing in a new session)

- Reviews real rendered output via screenshots constantly and gives
  precise, specific feedback (exact pixel judgments like "too much dead
  space," "shouldn't go all the way up") — treat these as real bug
  reports to root-cause, not vague taste comments to shrug off. Several
  turned out to be genuine bugs (see §6), not just polish requests.
- Sometimes phrases feedback in a way that reads ambiguous at first
  (e.g. "it doesn't go all the way up (not too much to overlap with the
  text)" meant "make it NOT go all the way up," not "confirming it
  currently doesn't") — when an instruction's literal grammar is
  ambiguous, interpret it against the concrete visual evidence/direction
  already established in the conversation rather than the most literal
  reading.
- Occasionally gives a fully-specified, very long feature brief (the
  `PipelineStages` rebuild) — for those, actually inspect the existing
  code and available dependencies before writing anything, and be
  willing to deviate from a specific literal instruction in the brief
  (e.g. "use GSAP") when the codebase's actual state makes a different
  choice clearly better, but say so explicitly rather than silently
  picking a different path.
- Wants real verification, not "should work" — this is why the
  Playwright probe workflow (§11) exists; use it for anything
  scroll/layout/animation-related rather than asserting correctness from
  reading the code alone.
- Explicit standing instruction: SimUX work happens only in
  `simux-poc/`, never in `site-doctor/`.
- The FYP-I hard gate ("M7 doesn't start until the landing page's design
  philosophy is confirmed settled") was explicitly lifted by direct
  instruction this session ("start M7") — don't re-litigate or ask for
  that confirmation again.

---

## 13. How to run what exists today

```bash
cd simux-poc
npm install
npm run dev      # http://localhost:5173
npm run build    # tsc -b && vite build — must be clean before considering any change done
npm run lint     # tsc --noEmit (same typecheck as build's first step)
```

No environment variables, no API keys, no backend to start — this is a
fully static Vite app.
