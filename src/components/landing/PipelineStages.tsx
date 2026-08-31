import { useRef, useState, type ReactNode } from "react";
import {
  AnimatePresence,
  motion,
  useMotionValue,
  useMotionValueEvent,
  useReducedMotion,
  useScroll,
  useTransform,
  type MotionStyle,
  type MotionValue,
} from "motion/react";
import { cn } from "@/lib/utils";
import { SeverityTag } from "@/components/SeverityTag";
import { VerifyStamp } from "@/components/VerifyStamp";
import { CountUp } from "@/components/CountUp";
import { PageMockup } from "@/components/personas/PageMockup";
import { AccessibilityRestrictedView, READING_ORDER } from "@/components/personas/AccessibilityRestrictedView";
import { MotorImprecisePointer } from "@/components/personas/MotorImprecisePointer";
import { useDemoRun } from "@/hooks/useDemoRun";
import { EASE } from "@/lib/motion";
import type { DemoRun, Finding, Persona, StageInfo } from "@/lib/types";

/**
 * Full rebuild, replacing the static 7-card grid with a scroll-driven
 * product walkthrough — the section now behaves like a pinned "watch
 * SimUX run" demo instead of a list of steps. Previous version (a
 * progress spine + 4/3-column card grid, each card revealing
 * independently on scroll) is gone entirely, not layered underneath.
 *
 * The whole story is built on ONE real fixture finding
 * (`a11y-checkout-continue-button` — accessibility persona, WCAG 2.2
 * SC 4.1.2, already has a full proposedFix/sandboxNote/verifyResult in
 * fixtures/demoRun.ts) rather than inventing generic placeholder
 * content — every card in every stage below is that same finding
 * moving through the pipeline, so "issue -> fix -> sandbox -> verify"
 * is one coherent thread, not seven unrelated illustrations. The
 * Aggregate stage is the only place other findings appear, exactly
 * because aggregation is where multiple findings actually converge.
 *
 * Animation library: `motion` (Framer Motion) — already the ONLY
 * animation dependency in this project (see package.json; no GSAP
 * anywhere). `useScroll({ target, offset: ["start start", "end end"] })`
 * against a tall `relative` section containing one `sticky top-0`
 * child gives exactly the pin-and-scrub behavior this section needs,
 * with scrollYProgress running 0->1 across the whole pinned duration
 * and reversing for free on scroll-up — no second animation library
 * needed. `activeStage` (discrete, 0-6) is the only piece of actual
 * React state driven by scroll, updated at most 6 times across the
 * entire scroll range; everything continuous (the crawl-stage outline
 * reveals) runs on MotionValues via useTransform, which don't trigger
 * React re-renders at all. This is deliberately NOT per-pixel
 * scroll-scrubbed for every visual (e.g. a persona cursor does not
 * track literal scroll position frame-by-frame) — each stage is a
 * scroll-controlled "scene" instead, which keeps the implementation
 * legible and performant while still fully satisfying "scroll down
 * advances it, scroll up reverses it, nothing plays on its own."
 *
 * Structural note carried over from CapabilityGrid.tsx's sticky-panel
 * work this session: the sticky child must be a DIRECT child of its
 * `relative` containing-block ancestor. An intermediate plain wrapper
 * div between them silently breaks `position: sticky` in this exact
 * Chromium build (verified via an isolated repro this session) — the
 * element still reports `position: sticky` via getComputedStyle but
 * never actually locks. Kept that constraint in mind throughout below.
 *
 * Below `lg`, and whenever `prefers-reduced-motion` is set (at ANY
 * width), the pinned/scrubbed experience is replaced entirely by
 * `MobileStages` — a plain stacked sequence, one block per stage, each
 * revealed via ordinary `whileInView` rather than scroll-jacking.
 * Scroll-jacked pinned sections are exactly the kind of motion a
 * reduced-motion user is asking to opt out of, and a pinned section on
 * a small viewport (address-bar collapse, awkward touch-scroll
 * physics) is a known bad combination — so both cases share the one
 * fallback rather than each getting a bespoke treatment.
 */

const TOTAL_STAGES = 7;
const TASK_LABEL = "Complete a purchase";

export function PipelineStages() {
  const run = useDemoRun();
  const reduce = useReducedMotion() ?? false;

  const persona = run.personas.find((p) => p.id === "accessibility")!;
  const finding = run.findings.find((f) => f.id === "a11y-checkout-continue-button")!;

  const sectionRef = useRef<HTMLElement>(null);
  const { scrollYProgress } = useScroll({
    target: sectionRef,
    offset: ["start start", "end end"],
  });

  const [activeStage, setActiveStage] = useState(0);
  useMotionValueEvent(scrollYProgress, "change", (v) => {
    const idx = Math.min(TOTAL_STAGES - 1, Math.max(0, Math.floor(v * TOTAL_STAGES)));
    setActiveStage((prev) => (prev === idx ? prev : idx));
  });

  // Seven explicit calls (not a .map loop) so this satisfies the rules
  // of hooks the same way CapabilityGrid's four useSectionInView calls
  // do — a fixed, known, always-seven-item count. Each is 0 outside its
  // own 1/7 slice of overall scroll and ramps 0->1 within it (clamped),
  // driving the Crawl stage's staggered outline reveal continuously.
  const p0 = useTransform(scrollYProgress, [0 / 7, 1 / 7], [0, 1]);
  const p1 = useTransform(scrollYProgress, [1 / 7, 2 / 7], [0, 1]);
  const p2 = useTransform(scrollYProgress, [2 / 7, 3 / 7], [0, 1]);
  const p3 = useTransform(scrollYProgress, [3 / 7, 4 / 7], [0, 1]);
  const p4 = useTransform(scrollYProgress, [4 / 7, 5 / 7], [0, 1]);
  const p5 = useTransform(scrollYProgress, [5 / 7, 6 / 7], [0, 1]);
  const p6 = useTransform(scrollYProgress, [6 / 7, 7 / 7], [0, 1]);
  const localProgress = [p0, p1, p2, p3, p4, p5, p6];

  return (
    <div id="how" className="scroll-mt-20 bg-ink">
      <MobileStages run={run} persona={persona} finding={finding} className={reduce ? "block" : "block lg:hidden"} />

      {!reduce && (
        <section ref={sectionRef} className="relative hidden h-[420vh] lg:block">
          <div className="sticky top-0 flex h-screen flex-col justify-center overflow-hidden py-10">
            <div className="container">
              <p className="font-mono text-micro uppercase tracking-wide text-paper/50">How it works</p>
              <h2 className="mt-3 font-hero text-d2 text-paper">Seven stages, one ranked report.</h2>
              <p className="mt-3 max-w-[54ch] text-sm leading-relaxed text-paper/60">
                Every run moves through the same pipeline, whichever personas you picked. Nothing here
                executes yet — this is what the finished version will do.
              </p>

              <div className="mt-10 grid gap-10 lg:grid-cols-[minmax(0,1fr)_460px] lg:items-center lg:gap-16">
                <div className="relative min-h-[180px]">
                  <AnimatePresence>
                    <motion.div
                      key={activeStage}
                      initial={{ opacity: 0, y: 16 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, y: -16 }}
                      transition={{ duration: 0.45, ease: EASE }}
                      className="absolute inset-0"
                    >
                      <span className="font-mono text-[0.6875rem] uppercase tracking-wide text-paper/40">
                        Stage {String(activeStage + 1).padStart(2, "0")} / 07
                      </span>
                      <h3 className="mt-3 font-display text-2xl font-bold tracking-tight text-paper md:text-3xl">
                        {run.stages[activeStage].label}
                      </h3>
                      <p className="mt-3 max-w-[42ch] text-[0.9375rem] leading-relaxed text-paper/65">
                        {run.stages[activeStage].description}
                      </p>
                    </motion.div>
                  </AnimatePresence>
                  {/* Sizing spacer — same technique as CapabilityGrid's panel:
                      the animated block above is absolutely positioned so
                      outgoing/incoming stage text can crossfade without a
                      layout jump, and this invisible copy holds the height. */}
                  <div className="invisible">
                    <span className="font-mono text-[0.6875rem] uppercase tracking-wide">Stage 01 / 07</span>
                    <h3 className="mt-3 font-display text-2xl font-bold md:text-3xl">{run.stages[0].label}</h3>
                    <p className="mt-3 max-w-[42ch] text-[0.9375rem] leading-relaxed">
                      {run.stages[0].description}
                    </p>
                  </div>
                </div>

                <div className="relative min-h-[420px] w-full">
                  {/* Absolutely positioned during the crossfade, same
                      reason as the left column's spacer trick above:
                      each stage's visual is a different height (the
                      persona reading-order list is much taller than,
                      say, the fix card), and without this, the outgoing
                      and incoming stage both contributing to normal-flow
                      height at once made the tallest one overflow
                      upward into the heading text above during the
                      transition. `min-h-[420px]` is sized for the
                      tallest stage (persona attempts); shorter stages
                      just center within the extra space. */}
                  <AnimatePresence>
                    <motion.div
                      key={activeStage}
                      initial={{ opacity: 0, scale: 0.96 }}
                      animate={{ opacity: 1, scale: 1 }}
                      exit={{ opacity: 0, scale: 0.96 }}
                      transition={{ duration: 0.45, ease: EASE }}
                      className="absolute inset-0 flex items-center justify-center"
                    >
                      <StageVisual
                        index={activeStage}
                        run={run}
                        persona={persona}
                        finding={finding}
                        local={localProgress[activeStage]}
                      />
                    </motion.div>
                  </AnimatePresence>
                </div>
              </div>

              <PipelineIndicator stages={run.stages} activeStage={activeStage} progress={scrollYProgress} />
            </div>
          </div>
        </section>
      )}
    </div>
  );
}

// Exported — Running.tsx (M8) reuses this directly so the live
// walkthrough and this landing-page preview never show two different
// visual languages for the same pipeline. Its sub-components
// (PersonaVisual, FixVisual, VerifyVisual) branch on `persona.id`/
// `finding.id` rather than assuming accessibility — Running.tsx passes
// whichever persona was actually selected on the New Run screen; this
// file's own two call sites (below) keep passing the accessibility
// persona/finding, unchanged.
export function StageVisual({
  index,
  run,
  persona,
  finding,
  local,
}: {
  index: number;
  run: DemoRun;
  persona: Persona;
  finding: Finding;
  local: MotionValue<number>;
}) {
  switch (index) {
    case 0:
      return <CrawlVisual local={local} />;
    case 1:
      return <PersonaVisual persona={persona} task={TASK_LABEL} />;
    case 2:
      return <GroundVisual finding={finding} />;
    case 3:
      return <FixVisual finding={finding} />;
    case 4:
      return <SandboxVisual />;
    case 5:
      return <VerifyVisual persona={persona} finding={finding} />;
    case 6:
      return <AggregateVisual run={run} />;
    default:
      return null;
  }
}

/* -------------------------------------------------------------------------
   Stage 1 — Crawl
------------------------------------------------------------------------- */

function CrawlVisual({ local }: { local: MotionValue<number> }) {
  const contentOpacity = useTransform(local, [0.05, 0.3], [0, 1]);
  const formOpacity = useTransform(local, [0.35, 0.6], [0, 1]);
  const ctaOpacity = useTransform(local, [0.65, 0.9], [0, 1]);

  return (
    <BrowserChrome>
      <div className="relative w-[280px]">
        <PageMockup />
        <StructureOutline style={{ opacity: contentOpacity }} rect="top-[50px] h-[48px]" label="content" />
        <StructureOutline style={{ opacity: formOpacity }} rect="top-[114px] h-[26px]" label="form" />
        <StructureOutline style={{ opacity: ctaOpacity }} rect="top-[154px] h-[36px]" label="cta" />
      </div>
    </BrowserChrome>
  );
}

function StructureOutline({ style, rect, label }: { style: MotionStyle; rect: string; label: string }) {
  // These overlay PageMockup, which has a LIGHT (bg-paper-raised) card
  // background, not the dark section chrome around it — dark ink tones
  // here, not the paper/light tones used everywhere else in this file.
  // A `border-paper/60` outline on a paper-colored card was previously
  // invisible; caught via computed-style inspection, not by eye.
  return (
    <motion.div
      style={style}
      className={cn("pointer-events-none absolute inset-x-4 rounded-[3px] border border-dashed border-ink/45", rect)}
    >
      <span className="absolute -top-4 left-0 whitespace-nowrap font-mono text-[0.5625rem] uppercase tracking-wide text-ink-3">
        {label}
      </span>
    </motion.div>
  );
}

function BrowserChrome({ children }: { children: ReactNode }) {
  return (
    <div className="overflow-hidden rounded-lg border border-paper/15 bg-ink shadow-[0_30px_70px_-30px_rgba(0,0,0,0.7)]">
      <div className="flex items-center gap-1.5 border-b border-paper/10 bg-paper/[0.04] px-3 py-2.5">
        <span className="h-2 w-2 rounded-full bg-paper/25" aria-hidden="true" />
        <span className="h-2 w-2 rounded-full bg-paper/25" aria-hidden="true" />
        <span className="h-2 w-2 rounded-full bg-paper/25" aria-hidden="true" />
        <span className="ml-3 rounded-sm bg-paper/[0.06] px-2 py-0.5 font-mono text-[0.625rem] text-paper/40">
          marlow.example/checkout
        </span>
      </div>
      <div className="flex justify-center bg-paper/[0.03] p-7">{children}</div>
    </div>
  );
}

/* -------------------------------------------------------------------------
   Stage 2 — Persona attempts
------------------------------------------------------------------------- */

const PERSONA_DOT: Record<string, string> = {
  accessibility: "bg-persona-accessibility",
  motor: "bg-persona-motor",
};

function PersonaVisual({ persona, task }: { persona: Persona; task: string }) {
  return (
    <div className="flex w-full max-w-[300px] flex-col items-center gap-4">
      <div className="flex flex-wrap items-center justify-center gap-x-4 gap-y-1.5">
        <span className="inline-flex items-center gap-1.5 font-mono text-[0.625rem] uppercase tracking-wide text-paper/60">
          <span className={cn("h-1.5 w-1.5 rounded-full", PERSONA_DOT[persona.id])} aria-hidden="true" />
          {persona.name}
        </span>
        <span className="text-paper/25" aria-hidden="true">
          ·
        </span>
        <span className="font-mono text-[0.625rem] uppercase tracking-wide text-paper/45">Task: {task}</span>
      </div>
      {persona.id === "motor" ? (
        // Motor's actual restriction (imprecise clicks) needs to be SEEN
        // happening, not read as a list — "full" size here, unlike
        // accessibility's thumbnail-plus-list below, since there's no
        // separate text readout for this persona to show instead.
        <MotorImprecisePointer size="full" active />
      ) : (
        <>
          {/* Thumbnail only, not AccessibilityRestrictedView's "full"
              2-column grid — that variant needs ~500px+ (280px mockup +
              a readable list column) and this stage's column is ~460px
              at most. The list below is built directly from the same
              exported READING_ORDER instead, stacked under the
              thumbnail rather than beside it. */}
          <AccessibilityRestrictedView size="thumbnail" active />
          <div className="w-full rounded-md border border-rule bg-paper-sunk p-3.5">
            <p className="mb-2 font-mono text-[0.5625rem] uppercase tracking-wide text-ink-3">
              What it actually perceives
            </p>
            <ol className="space-y-1 font-mono text-xs text-ink-2">
              {READING_ORDER.map((line, i) => (
                <li
                  key={i}
                  className={cn(
                    "border-b border-rule/60 py-1 last:border-0",
                    i === READING_ORDER.length - 1 && "text-critical",
                  )}
                >
                  {i + 1}. {line}
                </li>
              ))}
            </ol>
          </div>
        </>
      )}
    </div>
  );
}

/* -------------------------------------------------------------------------
   Stage 3 — Ground
------------------------------------------------------------------------- */

function GroundVisual({ finding }: { finding: Finding }) {
  const citation = finding.citation!;
  return (
    <div className="w-full max-w-[340px] space-y-2.5">
      <GroundCard eyebrow="Candidate issue">
        <p className="text-sm font-semibold leading-snug text-paper">{finding.title}</p>
      </GroundCard>
      <Arrow />
      <GroundCard eyebrow={citation.id}>
        <p className="text-sm font-semibold leading-snug text-paper">{citation.title}</p>
        <p className="mt-2 font-body text-xs italic leading-relaxed text-paper/55">
          &ldquo;{citation.text.slice(0, 110)}…&rdquo;
        </p>
      </GroundCard>
      <Arrow />
      <div className="flex items-center justify-center gap-2 rounded-md border border-[hsl(var(--minor))]/35 bg-[hsl(var(--minor))]/10 px-3 py-2.5">
        <DrawnCheck />
        <span className="font-mono text-[0.6875rem] uppercase tracking-wide text-paper/80">Validated finding</span>
      </div>
    </div>
  );
}

function GroundCard({ eyebrow, children }: { eyebrow: string; children: ReactNode }) {
  return (
    <div className="rounded-md border border-paper/15 bg-paper/[0.04] p-3.5">
      <p className="font-mono text-[0.5625rem] uppercase tracking-wide text-paper/40">{eyebrow}</p>
      <div className="mt-1.5">{children}</div>
    </div>
  );
}

function Arrow() {
  return (
    <div className="flex justify-center text-paper/25" aria-hidden="true">
      ↓
    </div>
  );
}

/* -------------------------------------------------------------------------
   Stage 4 — Propose fix
------------------------------------------------------------------------- */

// Small, abstract code-flavor tag per showcase finding — deliberately
// NOT trying to be a real diff or a general-purpose renderer for
// arbitrary findings; there are exactly two showcase findings in this
// POC (POC_SPEC.md §6 item 5), so a direct lookup is more honest than a
// generalized "generate a snippet from a finding" abstraction would be.
const FIX_SNIPPETS: Record<string, string> = {
  "a11y-checkout-continue-button": 'aria-label="Continue to payment"',
  "motor-checkout-apply-button-size": "min-width: 24px; min-height: 24px",
};

// Exported alongside StageVisual — FindingDetail.tsx (M10) reuses these
// three directly for its own fix -> sandbox -> verify walkthrough (the
// two showcase findings only), so that walkthrough and this landing
// page's/Running.tsx's previews of the same pipeline never drift into
// different visual languages for the same three steps.
export function FixVisual({ finding }: { finding: Finding }) {
  const snippet = FIX_SNIPPETS[finding.id];
  return (
    <div className="w-full max-w-[340px] space-y-2.5">
      <GroundCard eyebrow="Issue">
        <p className="text-sm leading-snug text-paper/70">{finding.title}</p>
      </GroundCard>
      <Arrow />
      <div className="rounded-md border border-[hsl(var(--minor))]/35 bg-[hsl(var(--minor))]/10 p-3.5">
        <p className="font-mono text-[0.5625rem] uppercase tracking-wide text-[hsl(var(--minor))]">Proposed fix</p>
        <p className="mt-1.5 text-sm leading-relaxed text-paper">{finding.showcase!.proposedFix}</p>
        {snippet && (
          <p className="mt-3 w-fit rounded-sm bg-ink px-2 py-1 font-mono text-[0.625rem] text-paper/55">{snippet}</p>
        )}
      </div>
    </div>
  );
}

/* -------------------------------------------------------------------------
   Stage 5 — Sandbox
------------------------------------------------------------------------- */

export function SandboxVisual() {
  return (
    <div className="w-full max-w-[440px]">
      <div className="grid grid-cols-2 gap-5">
        <div>
          <p className="mb-2 text-center font-mono text-[0.5625rem] uppercase tracking-wide text-paper/40">
            Live site · untouched
          </p>
          <div className="opacity-55 grayscale">
            <PageMockup className="mx-auto origin-top scale-[0.7]" />
          </div>
        </div>
        <div>
          <p className="mb-2 text-center font-mono text-[0.5625rem] uppercase tracking-wide text-[hsl(var(--minor))]">
            SimUX sandbox
          </p>
          <div className="relative">
            <PageMockup className="mx-auto origin-top scale-[0.7]" />
            <span className="absolute -bottom-2.5 left-1/2 -translate-x-1/2 whitespace-nowrap rounded-full border border-[hsl(var(--minor))]/40 bg-ink px-2 py-0.5 font-mono text-[0.5rem] text-[hsl(var(--minor))]">
              fix applied
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}

/* -------------------------------------------------------------------------
   Stage 6 — Verify
------------------------------------------------------------------------- */

export function VerifyVisual({ persona, finding }: { persona: Persona; finding: Finding }) {
  return (
    <div className="w-full max-w-[320px] space-y-4">
      <p className="font-mono text-[0.625rem] uppercase tracking-wide text-paper/45">{persona.name}</p>
      <div className="flex items-center gap-3">
        <span className="inline-flex items-center gap-1.5 text-paper/45">
          <DrawnX />
          <span className="text-xs">Attempt 01</span>
        </span>
        <span className="text-paper/25" aria-hidden="true">
          →
        </span>
        <span className="inline-flex items-center gap-1.5 text-[hsl(var(--minor))]">
          <DrawnCheck />
          <span className="text-xs">Attempt 02</span>
        </span>
      </div>
      <div className="rounded-md border border-paper/15 bg-paper/[0.04] p-3.5">
        <p className="font-mono text-xs leading-relaxed text-paper/70">{finding.recommendation}</p>
      </div>
      <VerifyStamp result={finding.showcase!.verifyResult} />
    </div>
  );
}

/* -------------------------------------------------------------------------
   Stage 7 — Aggregate
------------------------------------------------------------------------- */

const SEVERITY_RANK: Record<Finding["severity"], number> = { high: 0, medium: 1, low: 2 };

function AggregateVisual({ run }: { run: DemoRun }) {
  const ranked = [...run.findings].sort((a, b) => SEVERITY_RANK[a.severity] - SEVERITY_RANK[b.severity]).slice(0, 3);
  const high = run.findings.filter((f) => f.severity === "high").length;
  const medium = run.findings.filter((f) => f.severity === "medium").length;
  const low = run.findings.filter((f) => f.severity === "low").length;

  return (
    <div className="w-full max-w-[380px] space-y-4">
      <div className="flex items-center justify-between gap-4 rounded-md border border-paper/15 bg-paper/[0.04] p-4">
        <div>
          <p className="font-mono text-[0.5625rem] uppercase tracking-wide text-paper/40">UI Score</p>
          <p className="mt-1 font-hero text-4xl font-bold text-paper">
            <CountUp to={run.uiScore.composite} />
          </p>
        </div>
        <div className="space-y-1 font-mono text-[0.6875rem]">
          <p className="text-critical">{high} high</p>
          <p className="text-caution">{medium} medium</p>
          <p className="text-[hsl(var(--minor))]">{low} low</p>
        </div>
      </div>
      <ol className="space-y-2">
        {ranked.map((f, i) => (
          <li
            key={f.id}
            className="flex items-center gap-2.5 rounded-md border border-paper/10 bg-paper/[0.03] px-3 py-2"
          >
            <span className="font-mono text-[0.625rem] text-paper/35">#{i + 1}</span>
            <SeverityTag severity={f.severity} />
            <span className="truncate text-xs text-paper/75">{f.title}</span>
          </li>
        ))}
      </ol>
    </div>
  );
}

/* -------------------------------------------------------------------------
   Shared small marks
------------------------------------------------------------------------- */

function DrawnCheck() {
  return (
    <svg viewBox="0 0 24 24" className="h-3.5 w-3.5 shrink-0" fill="none" stroke="currentColor" strokeWidth={2.5} strokeLinecap="round" strokeLinejoin="round">
      <path d="M20 6 9 17l-5-5" />
    </svg>
  );
}

function DrawnX() {
  return (
    <svg viewBox="0 0 24 24" className="h-3.5 w-3.5 shrink-0" fill="none" stroke="currentColor" strokeWidth={2.5} strokeLinecap="round">
      <line x1="18" y1="6" x2="6" y2="18" />
      <line x1="6" y1="6" x2="18" y2="18" />
    </svg>
  );
}

/* -------------------------------------------------------------------------
   Pipeline indicator
------------------------------------------------------------------------- */

function PipelineIndicator({
  stages,
  activeStage,
  progress,
}: {
  stages: StageInfo[];
  activeStage: number;
  progress: MotionValue<number>;
}) {
  return (
    <div className="mt-10 lg:mt-12">
      <div className="relative h-px w-full bg-paper/15">
        <motion.div
          style={{ scaleX: progress }}
          className="absolute inset-y-0 left-0 w-full origin-left bg-paper/70"
        />
      </div>
      <div className="mt-4 flex items-center justify-between">
        {stages.map((stage, i) => (
          <div key={stage.id} className="flex flex-col items-center gap-1">
            <span
              className={cn(
                "font-mono text-[0.6875rem] tabular-nums transition-colors duration-300",
                i === activeStage ? "text-paper" : i < activeStage ? "text-paper/55" : "text-paper/25",
              )}
            >
              {String(i + 1).padStart(2, "0")}
            </span>
          </div>
        ))}
      </div>
      <div className="relative mt-2 h-4 text-center">
        <AnimatePresence>
          <motion.p
            key={activeStage}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.3 }}
            className="absolute inset-x-0 font-mono text-[0.6875rem] uppercase tracking-wide text-paper/60"
          >
            {stages[activeStage].label}
          </motion.p>
        </AnimatePresence>
      </div>
    </div>
  );
}

/* -------------------------------------------------------------------------
   Mobile / reduced-motion fallback — plain stacked sequence, no pinning,
   no scroll-scrub. Reuses the same per-stage visual components above so
   the two experiences never drift apart in content, only in how that
   content is revealed (whileInView-on-mount here, vs. scroll-scrubbed
   above).
------------------------------------------------------------------------- */

function MobileStages({
  run,
  persona,
  finding,
  className,
}: {
  run: DemoRun;
  persona: Persona;
  finding: Finding;
  className?: string;
}) {
  // Crawl's outline reveal takes a MotionValue driven by real scroll
  // progress on desktop; here there is no scroll-scrub to drive it, so
  // a constant "fully revealed" value stands in — the outlines just
  // appear already drawn when the block scrolls into view instead of
  // staggering in, which is the right simplification for a
  // non-scroll-jacked fallback.
  const staticProgress = useMotionValue(1);

  return (
    <div className={cn("py-16", className)}>
      <div className="container">
        <p className="font-mono text-micro uppercase tracking-wide text-paper/50">How it works</p>
        <h2 className="mt-3 font-hero text-d2 text-paper">Seven stages, one ranked report.</h2>
        <p className="mt-3 max-w-[54ch] text-sm leading-relaxed text-paper/60">
          Every run moves through the same pipeline, whichever personas you picked. Nothing here executes
          yet — this is what the finished version will do.
        </p>

        <ol className="mt-12 space-y-14">
          {run.stages.map((stage, i) => (
            <motion.li
              key={stage.id}
              initial={{ opacity: 0, y: 24 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, amount: 0.3 }}
              transition={{ duration: 0.6, ease: EASE }}
            >
              <span className="font-mono text-[0.6875rem] uppercase tracking-wide text-paper/40">
                Stage {String(i + 1).padStart(2, "0")} / 07
              </span>
              <h3 className="mt-2 font-display text-xl font-bold tracking-tight text-paper">{stage.label}</h3>
              <p className="mt-2 max-w-[48ch] text-sm leading-relaxed text-paper/65">{stage.description}</p>
              <div className="mt-6 flex justify-center">
                <StageVisual index={i} run={run} persona={persona} finding={finding} local={staticProgress} />
              </div>
            </motion.li>
          ))}
        </ol>
      </div>
    </div>
  );
}
