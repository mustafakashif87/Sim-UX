# DESIGN.md — SimUX POC visual design system

This describes the **currently implemented** design system, not a
proposal. It was originally built by studying wisprflow.ai's marketing
site (see §9, "Provenance," for that original research and what was and
wasn't kept) and has since evolved substantially through direct
implementation and iteration — every value below is the actual current
token, taken from `src/index.css` and `tailwind.config.js`, not an
aspiration. If you're about to style something, read this file, not
your memory of what the site used to look like.

---

## 1. Color

All colors are HSL triples stored as CSS custom properties in
`src/index.css`, consumed through `tailwind.config.js`'s `colors`
extension (e.g. `bg-paper`, `text-ink-2`, `border-critical`).

### Paper / ink (the base pair — carries ~90% of every screen)

| Token | HSL | Role |
|---|---|---|
| `--paper` | `60 100% 96%` | Page background. Exact HSL conversion of RGB `255,255,237` — a warm cream, deliberately requested at that exact value (an earlier, more conservative/desaturated cream was tried and explicitly overridden — see §9). |
| `--paper-raised` | `60 100% 98%` | Cards/surfaces that sit slightly "above" the page (e.g. `card-chart`) |
| `--paper-sunk` | `55 40% 93%` | Recessed surfaces (inputs, secondary panels) |
| `--ink` | `160 16% 7.5%` | Primary text + the site's one dark-section background (`bg-ink`). Near-black, not pure black. |
| `--ink-2` | `150 8% 30%` | Secondary text (body copy inside cards) |
| `--ink-3` | `155 6% 41%` | Tertiary text (labels, meta) |
| `--rule` | `129 9% 85%` | The one hairline border color used everywhere |

### Neutral stock tints (5 near-white variants, for non-persona card rotation)

`--stock-1` through `--stock-5` — very light, barely-differentiated
tints (`90 20% 98%`, `120 16% 96.8%`, `155 14% 96%`, `72 18% 97.2%`,
`175 12% 96.4%`). Used to give a grid of otherwise-identical cards a
tiny bit of visual variety without introducing real color. **Never**
combine these with severity or persona tinting on the same card.

### Severity (functional — never decorative, never touched for "harmony")

| Token | HSL | Paired `-ink` variant (for text on the light bg) |
|---|---|---|
| `--critical` | `3 62% 48%` | `--critical-ink`: `3 76% 40%` |
| `--caution` | `38 97% 37%` | `--caution-ink`: `38 98% 28%` |
| `--minor` | `153 47% 33%` | `--minor-ink`: `155 50% 24%` |

These carry real meaning (high/medium/low) and must stay legible and
internally consistent. **Do not** adjust these to better match the
warmer palette — that was tried once (an early, incorrect assumption
that a warmer palette needed a less-saturated paper background to keep
severity colors legible) and explicitly reversed once the actual
contrast math was checked: the lightness gap between these colors and
a 96%-lightness background is large regardless of the background's
saturation.

**On a dark (`bg-ink`) section**, do not reuse the `-ink` variants for
text (they're tuned for light backgrounds and read as too dark/muddy on
near-black). Use the base token instead: `text-critical`, `text-caution`,
`text-[hsl(var(--minor))]`.

### Persona tints (SimUX-specific — not present in the original ported base)

| Token | HSL | Paired `-ink` variant |
|---|---|---|
| `--persona-accessibility` | `258 42% 93%` (pastel lavender-blue) | `258 35% 32%` |
| `--persona-motor` | `335 50% 94%` (pastel rose) | `335 40% 30%` |
| `--persona-phase2` | `210 6% 91%` (neutral grey — NOT a third persona hue) | `210 6% 40%` |

Chosen specifically to sit outside the severity hues (critical ≈3°,
caution ≈38°, minor ≈153°) so a persona-colored card can never be
mistaken for a severity signal. `persona-phase2` is deliberately
desaturated grey — it marks "inert placeholder" (mobile-first), not a
third persona identity, and must never get its own saturated hue.

**Tinting rule, absolute:** severity tinting and persona tinting never
apply to the same card. Persona-grouped views (persona-selection cards,
results-grouped-by-persona) use persona tint exclusively; severity/plain
views keep the neutral `stock` rotation.

---

## 2. Typography

```js
// tailwind.config.js
fontFamily: {
  display: ["'Bricolage Grotesque'", "ui-sans-serif", "system-ui", "sans-serif"],
  body:    ["'Source Serif 4'", "Georgia", "ui-serif", "serif"],
  mono:    ["'IBM Plex Mono'", "ui-monospace", "SFMono-Regular", "monospace"],
  hero:    ["'Instrument Serif'", "'Source Serif 4'", "Georgia", "ui-serif", "serif"],
}
```

| Face | Used for | Notes |
|---|---|---|
| **Bricolage Grotesque** (`font-display`) | The default for ALL headings (`h1`-`h4` forced via `@layer base`), UI labels, buttons, nav | Deliberately swapped from Archivo, which reads as one of the most common "default AI-template" heading fonts right now. Bricolage has real character in its letterforms while staying fully professional — this was an explicit, considered swap, not a style preference to second-guess. |
| **Source Serif 4** (`font-body`) | ALL body copy, everywhere, including inside cards | Never used for hero-scale text — that's `font-hero`'s job exclusively. |
| **Instrument Serif** (`font-hero`) | ONLY hero-scale (`text-d1`/`text-d2`) headlines — Landing's H1, `SectionHeading`'s title, the Results UI Score numeral (once built) | Reserved specifically because its *italic* is genuinely elegant/calligraphic, not just slanted roman — this enables the roman+italic emphasis device used in Hero.tsx ("Some users can't see your screen." / "_Test like it._"), matching a wisprflow.ai reference. Swapped from an earlier Fraunces choice for this exact reason. Apply `font-hero` as a utility class directly on the element — Tailwind's layer ordering means a utility class beats the `@layer base` `h1..h4` rule with no `!important` needed. |
| **IBM Plex Mono** (`font-mono`) | Reserved for genuinely code-like content ONLY: page URLs, DOM/CSS selectors, confidence percentages, WCAG citation IDs (`.label-mono` class) | **Do not** reach for this by default for section eyebrows/labels — see the sentence-case alternative below. This distinction is deliberate and has been re-affirmed multiple times; don't collapse it back into "mono = all labels." |

### The two label styles — both real, used for different things

```css
/* index.css @layer components */
.label-mono   { @apply font-mono text-label font-medium uppercase text-ink-3; }
.eyebrow-sans { @apply font-display text-sm font-medium tracking-[0.08em] text-ink-3; }
```

- **`.label-mono`** — uppercase tracked monospace. For content that IS
  actually code-like (a WCAG ID, a confidence score, a URL).
- **`.eyebrow-sans`** — sentence-case tracked sans (weight 500,
  `tracking-[0.08em]`, ~70% ink opacity). For editorial section labels
  (`SectionHeading`'s eyebrow prop). This is the DEFAULT for "quiet
  metadata label" — reaching for `.label-mono` here out of habit is the
  single most common thing to get wrong when porting a pattern from an
  older sibling project.

### Type scale (fluid, `clamp()`-based)

| Token | Size | Line-height | Letter-spacing |
|---|---|---|---|
| `text-d1` | `clamp(2.75rem, 7vw, 5.25rem)` | `0.94` | `-0.035em` |
| `text-d2` | `clamp(2rem, 4.4vw, 3.25rem)` | `1.02` | `-0.028em` |
| `text-d3` | `clamp(1.375rem, 2.2vw, 1.75rem)` | `1.15` | `-0.018em` |
| `text-label` | `0.6875rem` | `1rem` | `0.14em` |
| `text-micro` | `0.625rem` | `0.875rem` | `0.16em` |

Body text: `1rem` / `1.65` line-height, `text-rendering: optimizeLegibility`.

---

## 3. Spacing, radius, shadow

### Container

```js
container: {
  center: true,
  padding: { DEFAULT: "1.25rem", sm: "2rem", lg: "2.5rem" },
  screens: { "2xl": "1200px" },
}
```

### Two-tier border radius

- **Tight tier** (buttons, tags, inputs, small UI elements): `lg: 0.5rem`,
  `md: 0.375rem`, `sm: 0.25rem` — unchanged from the ported base.
- **Soft tier** (section-level containers ONLY — persona cards, hero
  panels, `card-chart-lg`): `xl: 1.5rem`, `2xl: 2.5rem`. This is the
  single highest-leverage visual decision in the whole system: it's what
  separates "designed product" from "dev tool" more than any other one
  choice. Never apply the soft tier to a small UI element, or the tight
  tier to a section container.

### Shadow — two families, never mixed on the same element

```js
boxShadow: {
  chart: "0 1px 0 0 hsl(var(--rule)), 0 12px 32px -24px hsl(var(--ink) / 0.5)",
  lift:  "0 1px 0 0 hsl(var(--rule)), 0 20px 44px -28px hsl(var(--ink) / 0.55)",
  stamp:      "3px 3px 0 0 hsl(var(--ink))",
  "stamp-pass": "3px 3px 0 0 hsl(var(--minor))",
  "stamp-fail": "3px 3px 0 0 hsl(var(--critical))",
}
```

- **`.card-chart` / `.card-chart-lg`** (`@layer components`, `index.css`):
  hairline border + `shadow-chart` — the default "this is a card" surface,
  soft ambient elevation, meant to feel calm and flat.
- **`shadow-lift`** — the same family, slightly more elevation, used on
  hover for cards that should feel liftable (`PersonaCard`'s
  `hover:shadow-lift`).
- **`shadow-stamp*`** — hard, zero-blur, offset shadow. Deliberately the
  OPPOSITE treatment: reads as a physical sticker/stamp pressed onto the
  page, not a floating card. Reserved for exactly one thing:
  `VerifyStamp`'s pass/fail badge. Never use this family for a normal
  card, and never use the soft family for a verify stamp.

---

## 4. Motion system (`src/lib/motion.ts`)

**Library: `motion` (Framer Motion's `motion/react` package) — the only
animation dependency in this project.** No GSAP, deliberately (see
`CLAUDE.md` §4 for why this stayed true even under a brief that
suggested GSAP as "preferred").

- **`EASE = [0.16, 1, 0.3, 1]`** — the one curve for the whole product.
  "A machine part settling into place" — decelerates hard, never
  overshoots. Used via `transition(duration, delay)`.
- **No bounce/spring by default.** A small number of `type: "spring"`
  transitions exist as deliberate, scoped exceptions for genuine "pop"
  moments (Footer's dots dropping in, `CapabilityGrid`'s panel
  crossfade) — these are chosen on purpose, not drift from the system.
  Don't add a new spring without a specific reason, and don't "fix" an
  existing one to `EASE` without checking why it's there first.
- **Reveal variants**: `itemVariants` (rise), `fadeVariants` (arrive in
  place, for text inside an already-moving parent), `ruleVariants`
  (self-drawing hairline), `revealVariants` (card-sized: rise + scale +
  slight `rotateX` tilt + blur-in — pair with `perspective` on the
  parent), `revealFlatVariants` (same, no tilt, for flat rows),
  `wordVariants`/`wordContainerVariants` (per-word headline reveal, used
  by `SectionHeading` so a title reads itself into place a word at a
  time rather than appearing all at once).
- **`useParallax(target, distance)`** — subtle scroll-linked drift,
  keep `distance` small (≤ ~30px; past that it reads as "layout is
  broken," not "depth"). Respects `prefers-reduced-motion` (returns
  `undefined`, i.e. no transform applied, when reduced motion is on).
- **`prefers-reduced-motion: reduce`** is also handled globally in
  `index.css`: all animation/transition durations collapse to `0.001ms`,
  and `scroll-behavior` drops from `smooth` to `auto`.

### Scroll-pinned / scroll-scrubbed sections (the hard-won pattern)

Two sections in this codebase (`CapabilityGrid.tsx`,
`PipelineStages.tsx`) use a real pin-and-scrub pattern — this is
**exclusively** a `motion/react` `useScroll`/`useTransform`/
`useMotionValueEvent` construction, not CSS scroll-snap and not a second
library. The load-bearing rules, all found the hard way (full detail in
`CLAUDE.md` §6 and §§8-9):

1. **The sticky element must be a direct child of its `position:
   relative` (or otherwise positioned) containing-block ancestor.** Any
   plain wrapper `<div>` in between — even completely unstyled —
   silently breaks `position: sticky` in the Chromium build this project
   tests against. If you need to add spacing/offset before a sticky
   element, put it as padding on the containing block itself.
2. Prefer **fixed `px`** sizing over `vh` for anything sized around
   fixed-size text content inside a scroll-scrubbed layout — `vh`-based
   heights make dead space scale up (not down) on taller browser
   windows, since the content itself doesn't grow with viewport height.
3. `useScroll({ target, offset: ["start start", "end end"] })` reaches
   `scrollYProgress === 1` one viewport-height BEFORE the section's full
   CSS height is scrolled — this is correct (it's exactly the pinned
   duration), not a bug, and shows up as a natural "dwell" on whatever
   the final state is.
4. Discrete stage/scene switches should be driven by ONE piece of React
   state (updated via `useMotionValueEvent`, at most a handful of times
   across the whole scroll range), not per-pixel state updates.
   Continuous sub-animations (an outline fading in, a bar filling)
   should run on `useTransform`-derived `MotionValue`s directly in
   `style`, which never trigger a React re-render.
5. **Verify these sections with Playwright, not by eye** — see
   `CLAUDE.md` §11 for the exact probe pattern. Several real bugs in
   this pattern (the sticky-wrapper bug, an invisible-overlay-color bug)
   produced screenshots that looked plausible at a glance; only reading
   `getComputedStyle`/`getBoundingClientRect()` directly at the exact
   transition frame caught them.
6. **Always ship a non-pinned fallback**, shown below `lg` AND whenever
   `prefers-reduced-motion` is set (at any width) — reuse the exact same
   per-stage/per-item content components in both paths so they can't
   drift apart, and reveal them with a plain `whileInView` instead of
   scroll-scrubbing.

---

## 5. Persona visual language

The project's actual novelty claim is that persona restrictions are
genuine constraints, not roleplay — so every persona's UI treatment
exists specifically to make that restriction *visible*, not just
stated in a caption.

- **Accessibility-focused** (`AccessibilityRestrictedView.tsx`): a
  blurred + desaturated (`saturate(0.15)`) rendering of the page beside
  a plain linearized reading-order list — the literal metaphor is "this
  agent never receives the screenshot, only this list." Two sizes:
  `"thumbnail"` (64×80px, for at-rest cards) and `"full"` (needs ~500px+
  — a fixed 280px mockup plus a readable list column in a 2-column
  grid; **do not** force this variant into a narrower column, reuse the
  exported `READING_ORDER` array and build a single-column layout
  instead, as `PipelineStages` does).
- **Motor / age-related** (`MotorImprecisePointer.tsx`): an animated
  cursor that overshoots/misses a small target, pauses, then corrects —
  never aimless jitter, always a legible miss-then-correct sequence.
  Two sizes: `"icon"` and `"full"`.
- **Mobile-first**: Phase 2 / FYP-II placeholder, badged with the
  neutral `persona-phase2` tint — but as of M7, NOT visually or
  interactively diminished otherwise (no dimmed opacity, no disabled
  state, same hover/press treatment as the other two). The badge alone
  carries "not real yet"; reduced polish must not also carry that
  meaning; a card with a `dashed` border + "preview" label stands in for
  its metaphor thumbnail since no restriction-simulation exists for it.

### The dark-chrome / light-content browser convention

`PageMockup.tsx` — a fake "screenshot" of Marlow's checkout page, built
from real markup, not an image, and deliberately embodies three real
fixture findings (a too-small "Apply" button, a stepper whose minus
button sits too close to the input, an icon-only "Continue" button with
no accessible name). When wrapped in a "browser chrome" (as
`PipelineStages`' Crawl stage does), the chrome itself uses the DARK
section palette (`bg-ink`, `border-paper/15`, light text) while the
mockup content inside stays the site's normal LIGHT paper palette — this
reads as "a real browser window showing a real light website," which is
more convincing than making the whole thing dark. **Any overlay drawn on
top of `PageMockup`** (outlines, highlight rings, labels) must use DARK
tones (`border-ink/45`, `text-ink-3`) to actually be visible against
that light content — using the surrounding section's light/paper tones
for such an overlay is invisible (a real bug hit once, see `CLAUDE.md`
§6).

---

## 6. Iconography and marks

- **`lucide-react`** for all inline icons.
- **`BrandMark`**: three dots (one per persona) + wordmark. Replaced an
  inherited ECG/vitals-trace glyph — the mark itself now says "three
  personas," not "heart monitor," matching the removal of Site Doctor's
  clinical-instrument identity (§7).
- Drawn SVG marks (checkmarks, X's) are built as `motion.path`/
  `motion.line` with `pathLength: 0 -> 1` reveals (see `Comparison.tsx`'s
  `DrawnCheck`/`DrawnX`), not `lucide-react` icon components — lucide
  icons don't expose their internal path for this animation.

---

## 7. What was deliberately removed, and must not come back

- **The graph-paper grid background** (`body::before` in the ported
  base CSS) — Site Doctor's clearest "audit instrument / chart paper"
  visual signature. Removed entirely; plain paper background now, no
  texture.
- **`Trace.tsx`**, the ECG/vitals-trace ported component and its
  `animate-blip` keyframe — deleted, not hidden, along with the rest of
  the "clinical instrument" metaphor. If an old planning document
  mentions reusing it (M8's spine visual is the one place this still
  comes up), that reference is stale — build a fresh non-clinical
  replacement (a simple connecting line/dot-progression) instead.
- **The checkbox-list "pick checks to run" mental model** — Site
  Doctor's audit-category selection pattern. SimUX's equivalent is
  large persona cards with genuine selection semantics (Radix
  `ToggleGroup`/similar), never small checkbox toggles.

---

## 8. What NOT to import from the original Wispr research (§9)

- Their multi-hue pastel accent set (`signal` pink, `flare` orange,
  `glow` amber, `pulse` maroon) — never used; would compete with the
  functional severity palette (§1). SimUX's persona tints are the only
  accent hues in the system, and they're deliberately restrained (one
  lavender, one rose, one neutral grey), not a rainbow.
- Uppercase mono as a universal label style — deliberately kept as a
  two-way split (§2) rather than picking one convention globally.
- Any duotone/gradient photography treatment — this project has no
  photography at all; every visual is built from real markup or a
  hand-drawn SVG metaphor, never a stock image or gradient-graded photo.

---

## 9. Provenance

This design system's warm-cream-paper / near-black-ink / restrained-
serif-display formula was originally derived by fetching
`wisprflow.ai`'s raw HTML and compiled CSS bundle directly (no browser
tooling was available in that early session) and extracting real values
— custom properties, computed class rules, `@font-face` declarations —
rather than impressions from a screenshot. That research covered Wispr's
color palette, type scale, spacing/radius/shadow vocabulary, and motion
timing in detail, and produced an initial proposed mapping onto this
project.

Most of that mapping has since been implemented and then evolved
further through direct iteration (the exact fonts changed twice, the
paper color's exact value was revisited and corrected once, the two-tier
label system and two-tier radius/shadow systems were adopted as
described, and the sticky-scroll motion patterns in §4 didn't exist in
that research at all — they were built and debugged from scratch this
project). This file now describes that current, implemented state as
the source of truth; the original raw research notes are not reproduced
here since they'd now be misleading as a "what to build" reference — the
building already happened. If a genuinely new visual question comes up
that this file doesn't answer, treat Wispr's actual current marketing
site as a live reference to re-check, not old notes to trust blindly —
their own site may have changed since that research was done.
