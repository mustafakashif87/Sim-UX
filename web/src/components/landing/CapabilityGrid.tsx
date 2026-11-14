import { useState, type ReactNode } from "react";
import { Quote, Wrench, Box, TrendingUp } from "lucide-react";
import { AnimatePresence, motion } from "motion/react";
import { SectionHeading } from "@/components/SectionHeading";
import { SeverityTag } from "@/components/SeverityTag";
import { VerifyStamp } from "@/components/VerifyStamp";
import { useDemoRun } from "@/hooks/useDemoRun";
import { useSectionInView } from "@/hooks/useActiveSection";
import { cn } from "@/lib/utils";

/**
 * M6b built this as a static 2x2 grid; M6c rebuilt it as a sticky-left/
 * scrolling-right section referenced against a live wisprflow.ai
 * screenshot. This pass (still M6c) fixes five specific problems found
 * once it was actually seen rendered:
 *
 * 1. Panel was a big-radius `card-chart-lg` "pill," sized to its own
 *    sparse content — now a fixed-size, tighter-radius `card-chart`
 *    rectangle, taller than the text beside it, same size for all four.
 * 2. Text column had a `max-w-[42ch]` cap inside a 50/50 grid, leaving
 *    the whole right half of the viewport empty — the grid is now
 *    `[400px_1fr]` (fixed panel column, flexible text column) with a
 *    wider cap, so text actually uses the space.
 * 3. Each scroll-block was `min-h-[55vh]` — cut to `min-h-[32vh]`.
 * 4. `AnimatePresence mode="wait"` waited for the exit animation to
 *    finish before mounting the next panel — on a fast scroll this is
 *    exactly "the pill disappears for too long." Removed `mode="wait"`
 *    (default sync mode crossfades old/new simultaneously, no gap).
 * 5. Each panel's content was sparse (one small element floating in a
 *    big box) — all four rebuilt with a real focal layout that fills
 *    the fixed size instead of leaving empty space around a tiny thing.
 *
 * Follow-up round, after actually seeing it render: the panel (420px)
 * was too large and, at that height against a 380-400px-wide column,
 * read closer to square than rectangular — cut to 260px (see `Panel`).
 * It was also overlapping the section heading when scrolled to the top
 * — a taller panel centered at 50% viewport height reaches further
 * upward, and there wasn't enough clearance below the heading before
 * the sticky container began; fixed by both shrinking the panel and
 * widening the heading-to-grid gap (`mt-24`, was `mt-14`). Separately,
 * the active index could get stuck one block early near the end of a
 * fast scroll — the center-band trigger (`useSectionInView`) was only
 * 10% of viewport tall, narrow enough to scroll straight past in one
 * frame, and since `onActive` never resets, a missed last block just
 * stays stuck on whichever fired before it. Widened to a 30%-tall band.
 *
 * Third round: tried a per-block sticky container (one independent
 * `sticky top-1/2` panel per item, each in its own `min-h-[90vh]` grid
 * row) instead of one shared panel — this correctly reproduced the
 * move-until-centered / lock-at-center / release three-phase behavior
 * per block, but broke a different, more basic expectation: at each
 * handoff, one panel element scrolled away and a SEPARATE panel
 * element scrolled in from below, instead of a single persistent panel
 * changing what it shows. It also made each block's own scroll
 * distance too long (90vh each, so ~360vh just for this section) and
 * reintroduced the heading-overlap bug, since with only a `mt-24` gap
 * below the heading, the FIRST block's sticky threshold (needing the
 * panel's static position within 50% of viewport height from the top)
 * could already be satisfied at initial scroll, before the heading had
 * cleared.
 *
 * Fourth round (current): back to ONE persistent sticky panel spanning
 * all four blocks, crossfading its content via the shared `active`
 * index (`AnimatePresence`, same pattern as the very first version of
 * this section) — restores "the same panel changes into the next
 * panel" instead of a new element appearing per block. `top-1/2
 * -translate-y-1/2` (true center) is kept, since that's the confirmed
 * correct resting position. The heading-overlap problem this reintroduces
 * is solved differently this time: instead of choosing a compromise
 * offset (which is what `top-28` was), a `pt-[55vh]` buffer sits
 * between the heading and the sticky panel, inside the same `relative`
 * column (this doesn't add visible dead space — the column's actual
 * rendered height is governed by the much-taller text column via CSS
 * Grid's default stretch, so the buffer only delays the panel's
 * *static* flow position, i.e. how much scroll is needed before the
 * sticky math would put it within 50% of viewport height from the top).
 * The result: the panel simply isn't shown yet during the brief span
 * where the heading is still in view — it appears for the first time
 * already locked at center, once you've scrolled enough for the first
 * block's center-lock point to be reached — which is arguably a more
 * literal match for "the panel should start [existing/mattering] once
 * it's centered" than any version that shows it moving beforehand.
 * Each text block's `min-h` was also cut (`90vh` -> `45vh`) to close up
 * the excess distance between blocks, closer to a live wisprflow.ai
 * reference showing the next block already partly visible below the
 * current one rather than a near-full-viewport gap.
 */
export function CapabilityGrid() {
  const run = useDemoRun();
  const citedFinding = run.findings.find((f) => f.citation)!;
  const taggedFinding = run.findings.find((f) => f.showcase && f.personaId === "motor")!;
  const taggedPersona = run.personas.find((p) => p.id === taggedFinding.personaId)!;
  const historyScores = [...run.history].reverse().map((h) => h.uiScore).concat(run.uiScore.composite);
  const [active, setActive] = useState(0);

  const items = [
    {
      label: "Grounded citations",
      heading: "Never model-recalled",
      body: "Every finding that cites a standard cites real, retrieved text — hand-verified against the actual WCAG or Nielsen source, never invented.",
      panel: (
        <Panel tint="bg-stock-1">
          <Quote className="h-5 w-5 text-ink-3/50" strokeWidth={1.5} />
          <p className="mt-2 flex-1 overflow-hidden font-body text-base italic leading-snug text-ink">
            &ldquo;{citedFinding.citation!.text.slice(0, 80)}…&rdquo;
          </p>
          <div className="mt-4 flex items-center justify-between border-t border-rule pt-3">
            <span className="font-mono text-[0.6875rem] uppercase tracking-wide text-ink-3">
              {citedFinding.citation!.id}
            </span>
            <span className="rounded-full bg-minor/15 px-2 py-0.5 font-mono text-[0.625rem] uppercase text-[hsl(var(--minor-ink))]">
              Verified
            </span>
          </div>
        </Panel>
      ),
    },
    {
      label: "Sandboxed & verified fixes",
      heading: "Proposed, then proven",
      body: "A fix is never just suggested. It's applied to an isolated copy of the page, then the same persona re-attempts the task to confirm it actually worked.",
      panel: (
        <Panel tint="bg-stock-4">
          <div className="flex flex-1 flex-col justify-center gap-3">
            <FixStep icon={Wrench} label="Proposed" />
            <StepConnector />
            <FixStep icon={Box} label="Sandboxed" />
            <StepConnector />
            <VerifyStamp result="pass" />
          </div>
        </Panel>
      ),
    },
    {
      label: "Persona-tagged findings",
      heading: "Traceable to a persona",
      body: "Every finding carries which persona surfaced it, so a reviewer can see exactly which restriction produced which piece of friction.",
      panel: (
        <Panel tint="bg-persona-motor">
          <div className="flex flex-1 flex-col justify-center">
            <div className="rounded-md border border-ink/10 bg-paper-raised p-4">
              <div className="flex flex-wrap items-center gap-2">
                <SeverityTag severity={taggedFinding.severity} />
                <span className="rounded-full border border-ink/15 bg-paper-sunk px-2.5 py-0.5 font-mono text-[0.625rem] text-ink-2">
                  {taggedPersona.name}
                </span>
              </div>
              <p className="mt-3 font-display text-sm font-bold leading-snug text-ink">
                {taggedFinding.title}
              </p>
            </div>
          </div>
        </Panel>
      ),
    },
    {
      label: "Run history",
      heading: "Regression, tracked",
      body: "Every run is compared against the ones before it, so a report shows whether things are actually getting better, not just what's wrong today.",
      panel: (
        <Panel tint="bg-stock-5">
          <div className="flex flex-1 flex-col items-center justify-center gap-6">
            <div className="text-center">
              <div className="font-hero text-5xl font-bold text-ink">{run.uiScore.composite}</div>
              <div className="mt-1 font-mono text-[0.625rem] uppercase tracking-wide text-ink-3">
                Current UI Score
              </div>
            </div>
            <div className="flex items-end gap-2.5">
              {historyScores.map((score, i) => (
                <div
                  key={i}
                  className={cn(
                    "w-6 rounded-t-sm",
                    i === historyScores.length - 1 ? "bg-ink" : "bg-ink/35",
                  )}
                  style={{ height: `${Math.max(14, score * 0.9)}px` }}
                />
              ))}
              <TrendingUp className="ml-1 h-5 w-5 text-[hsl(var(--minor-ink))]" />
            </div>
          </div>
        </Panel>
      ),
    },
  ];

  // Fixed count (4) — called explicitly, not in a loop, per rules of hooks.
  const ref0 = useSectionInView(0, setActive);
  const ref1 = useSectionInView(1, setActive);
  const ref2 = useSectionInView(2, setActive);
  const ref3 = useSectionInView(3, setActive);
  const refs = [ref0, ref1, ref2, ref3];

  return (
    <section className="border-t border-rule py-20 md:py-28">
      <div className="container">
        <SectionHeading
          eyebrow="What each run produces"
          title="Four things every report actually has."
        />

        {/* lg and up: ONE sticky panel, scroll-tracked text. Fixed-width
            left column (matches the panel's own fixed size) + flexible
            right column, instead of an even 50/50 split that left the
            text capped well short of the available width.

            grid-cols first value = panel width (widened 380->440px);
            gap widened 12->20 to push the text column further right —
            there was still dead space between the panel and the text,
            and past the end of each text line, that a bigger gap (not
            a wider text cap) is the more direct fix for, per feedback:
            move the text right, keep the panel's own position as-is.

            No top buffer on `.relative` anymore (the earlier `pt-[55vh]`
            was removed) — worked out the exact geometry instead of
            tuning by feel, per the spec: max-up should land exactly when
            the panel's center reaches the first block's top; max-down
            exactly when the panel's center reaches the last block's
            bottom. `position: sticky`'s ENGAGE condition only checks the
            element's top edge crossing the `top-1/2` threshold — it has
            NO dependency on the element's own height, and `.relative`'s
            top already equals the first block's top exactly (same grid
            row, same document position) — so with zero top padding,
            engage happens EXACTLY when the first block's top is at
            viewport center, which is EXACTLY when the (also-centered)
            panel's center is at that same point. No buffer needed or
            wanted here; one was only ever needed to compensate for
            insufficient clearance below the heading (see `mt-40` below).
            RELEASE is NOT symmetric, though — that condition DOES
            subtract the element's own height (`H`), so with zero extra
            room the sweep undershoots the last block's true bottom by
            exactly `H`. That's what the `+260px` on the last block below
            corrects — see that comment for the matching half of this
            same derivation. `mt-40` (was `mt-24`) is a separate, unrelated
            fix: purely heading clearance headroom, sized so the panel
            (`h-[260px]`, so half-height 130px) can lock at center without
            its top edge reaching up into the heading's own last line —
            needs `mt-* >= half the panel's height`; 160px comfortably
            clears the 130px minimum. */}
        <div className="mt-40 hidden lg:grid lg:grid-cols-[440px_1fr] lg:gap-20">
          <div className="relative">
            <div className="sticky top-1/2 -translate-y-1/2">
              <AnimatePresence>
                <motion.div
                  key={active}
                  initial={{ opacity: 0, scale: 0.92 }}
                  animate={{ opacity: 1, scale: 1 }}
                  exit={{ opacity: 0, scale: 0.92 }}
                  transition={{ type: "spring", stiffness: 300, damping: 20 }}
                  className="absolute inset-0"
                >
                  {items[active].panel}
                </motion.div>
              </AnimatePresence>
              {/* Sizing spacer — the animated panel above is absolutely
                  positioned (so outgoing/incoming panels can overlap
                  during the crossfade instead of the sync-mode pair
                  stacking and changing this box's height); this holds
                  the actual layout size. */}
              <div className="invisible">{items[0].panel}</div>
            </div>
          </div>

          <div className="flex flex-col">
            {items.map((item, i) => (
              <div
                key={item.label}
                ref={refs[i]}
                className={cn(
                  // Fixed px, not `vh` — `45vh` was the actual cause of
                  // "too much dead space between blocks" reported on a
                  // tall browser window: at a 900px viewport that's
                  // 405px per block, but on a taller one (the reported
                  // screenshot's window clearly was) it scales up
                  // further while the text content itself (~150px)
                  // stays the same size, so the gap gets WORSE the
                  // taller the window — a `vh` unit was the wrong choice
                  // for something sized around fixed text content. A
                  // fixed 320px reliably leaves a modest, constant
                  // margin around the centered text regardless of
                  // viewport height. The lock/release derivation below
                  // doesn't care whether this is `vh` or `px` — it only
                  // depends on `panel height` being added to the LAST
                  // block, not on this value's unit.
                  "flex min-h-[320px] flex-col justify-center",
                  // Sticky's RELEASE math subtracts the panel's own
                  // height from how far it can travel (unlike engage,
                  // which doesn't) — so with no compensation, release
                  // fires `panel height` (260px, matching Panel's own
                  // `h-[260px]`) short of the true last-block bottom.
                  // Extending only the LAST block's row by exactly that
                  // amount gives the sticky panel the missing runway, so
                  // release lands precisely at "panel's center reaches
                  // the last block's bottom" per spec, matching the
                  // first-block/top derivation in the comment above.
                  i === items.length - 1 && "min-h-[580px]",
                )}
              >
                <div
                  className={cn(
                    "transition-opacity duration-500",
                    active === i ? "opacity-100" : "opacity-35",
                  )}
                >
                  <p className="label-mono">{item.label}</p>
                  <h3 className="mt-3 font-display text-2xl font-bold text-ink">{item.heading}</h3>
                  <p className="mt-3 max-w-[60ch] text-[0.9375rem] leading-relaxed text-ink-2">{item.body}</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Below lg: no sticky/scroll-tracking, each block gets its own panel inline */}
        <div className="mt-14 space-y-10 lg:hidden">
          {items.map((item) => (
            <div key={item.label}>
              <div className="mb-4">{item.panel}</div>
              <p className="label-mono">{item.label}</p>
              <h3 className="mt-3 font-display text-2xl font-bold text-ink">{item.heading}</h3>
              <p className="mt-3 max-w-[60ch] text-[0.9375rem] leading-relaxed text-ink-2">{item.body}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

function Panel({ tint, children }: { tint: string; children: ReactNode }) {
  // h-[260px] (was 420px) — 420 read as too large and, at this width,
  // closer to square than rectangular; 260 against a 380px-wide column
  // is a clear landscape rectangle and leaves real clearance above it
  // when centered in the viewport.
  return (
    <div className={cn("card-chart flex h-[260px] w-full flex-col p-6", tint)}>
      {children}
    </div>
  );
}

function FixStep({ icon: Icon, label }: { icon: typeof Wrench; label: string }) {
  return (
    <div className="flex items-center gap-3">
      <span className="grid h-8 w-8 shrink-0 place-items-center rounded-md border border-ink/15 bg-paper-raised">
        <Icon className="h-4 w-4 text-ink-2" strokeWidth={1.75} />
      </span>
      <span className="font-mono text-sm text-ink-2">{label}</span>
    </div>
  );
}

function StepConnector() {
  return <div className="ml-4 h-3 w-px bg-ink/15" aria-hidden="true" />;
}
