import { useEffect, useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { AnimatePresence, motion, useMotionValue } from "motion/react";
import { SiteNav } from "@/components/SiteNav";
import { Footer } from "@/components/Footer";
import { StageVisual } from "@/components/landing/PipelineStages";
import { useDemoRun } from "@/hooks/useDemoRun";
import { cn } from "@/lib/utils";
import { EASE } from "@/lib/motion";

/**
 * M8 — the real running/execution-state screen, replacing the M4
 * placeholder. A SCRIPTED (fixed-duration, not simulated-live) walk
 * through the same 7 stages `PipelineStages` previews on the landing
 * page — reuses that file's exported `StageVisual` directly rather than
 * rebuilding the same seven cards a second time, so the landing-page
 * teaser and this actual walkthrough never drift into two different
 * visual languages for the same pipeline.
 *
 * "Driven by whichever persona(s) were picked" (the milestone's own
 * words): NewRun.tsx passes the selected persona ids via router
 * `state` (see the comment on that Link) — the smallest mechanism that
 * works, since nothing else in the app needs this value and its
 * lifetime should be exactly "until this run finishes." If accessed
 * directly (no state — e.g. a bookmarked/typed URL), falls back to the
 * accessibility persona, matching the richer of the two showcases.
 * Only accessibility and motor have real showcase findings
 * (`finding.showcase`) per POC_SPEC.md §6 item 5.
 *
 * Honesty rule (POC_SPEC.md §7 — "never imply live execution"): the
 * only thing timed here is a REAL, ticking elapsed-time display, driven
 * by a fixed, known stage-duration script — never a fake progress
 * percentage. The stage spine below states plainly this is scripted.
 */

const STAGE_DURATIONS_MS = [2500, 4000, 2500, 2500, 2500, 3000, 4000];
const TOTAL_MS = STAGE_DURATIONS_MS.reduce((a, b) => a + b, 0);

export default function Running() {
  const run = useDemoRun();
  const navigate = useNavigate();
  const location = useLocation();

  const routerState = location.state as { personaIds?: string[]; siteUrl?: string } | null;
  const personaIds = routerState?.personaIds ?? ["accessibility"];
  const siteUrl = routerState?.siteUrl;
  const activePersonaId = personaIds.includes("accessibility")
    ? "accessibility"
    : personaIds.includes("motor")
      ? "motor"
      : "accessibility";
  const persona = run.personas.find((p) => p.id === activePersonaId)!;
  const finding = run.findings.find((f) => f.personaId === activePersonaId && f.showcase)!;
  const taskLabel = run.tasks.find((t) => t.id === finding.taskId)?.label ?? finding.taskId;

  const [activeStage, setActiveStage] = useState(0);
  const [elapsedMs, setElapsedMs] = useState(0);
  const fillProgress = useMotionValue(0);
  const localProgress = useMotionValue(1); // CrawlVisual's outlines: show fully drawn, no scroll to scrub against here

  useEffect(() => {
    const startedAt = Date.now();
    let stageTimer: ReturnType<typeof setTimeout>;
    let tickTimer: ReturnType<typeof setInterval>;
    let cancelled = false;

    const scheduleStage = (index: number) => {
      if (index >= STAGE_DURATIONS_MS.length) {
        navigate("/results", { replace: true });
        return;
      }
      setActiveStage(index);
      stageTimer = setTimeout(() => {
        if (!cancelled) scheduleStage(index + 1);
      }, STAGE_DURATIONS_MS[index]);
    };
    scheduleStage(0);

    tickTimer = setInterval(() => {
      const ms = Date.now() - startedAt;
      setElapsedMs(ms);
      fillProgress.set(Math.min(1, ms / TOTAL_MS));
    }, 200);

    return () => {
      cancelled = true;
      clearTimeout(stageTimer);
      clearInterval(tickTimer);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps -- intentionally runs once per mount; re-running on navigate/fillProgress identity would restart the whole scripted sequence
  }, []);

  const elapsedLabel = `0:${String(Math.floor(elapsedMs / 1000)).padStart(2, "0")}`;

  return (
    <>
      <SiteNav variant="app" />
      <main className="container py-20 md:py-28">
        <p className="eyebrow-sans">Running</p>
        <h1 className="mt-3 font-hero text-d1 text-ink">Watching SimUX run.</h1>
        <p className="mt-4 max-w-[58ch] text-ink-2">
          A scripted walkthrough — nothing here executes against a real target. Elapsed:{" "}
          <span className="font-mono tabular-nums text-ink">{elapsedLabel}</span>
        </p>
        <p className="mt-2 font-mono text-[0.8125rem] text-ink-3">
          Target: {siteUrl || run.productName} — the walkthrough below is always {run.productName}'s
          fixture run, regardless of what was entered.
        </p>

        <div className="mt-12 grid gap-10 lg:grid-cols-[minmax(0,1fr)_460px] lg:items-center lg:gap-16">
          <div className="relative min-h-[160px]">
            <AnimatePresence>
              <motion.div
                key={activeStage}
                initial={{ opacity: 0, y: 16 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -16 }}
                transition={{ duration: 0.45, ease: EASE }}
                className="absolute inset-0"
              >
                <span className="font-mono text-[0.6875rem] uppercase tracking-wide text-ink-3">
                  Stage {String(activeStage + 1).padStart(2, "0")} / 07
                </span>
                <h2 className="mt-3 font-display text-2xl font-bold tracking-tight text-ink md:text-3xl">
                  {run.stages[activeStage].label}
                </h2>
                <p className="mt-3 max-w-[42ch] text-[0.9375rem] leading-relaxed text-ink-2">
                  {run.stages[activeStage].description}
                </p>
              </motion.div>
            </AnimatePresence>
            {/* Sizing spacer — same technique as PipelineStages' own left
                column: the animated block above is absolutely
                positioned so outgoing/incoming stage text can crossfade
                without a layout jump, and this invisible copy holds
                the height. */}
            <div className="invisible">
              <span className="font-mono text-[0.6875rem] uppercase tracking-wide">Stage 01 / 07</span>
              <h2 className="mt-3 font-display text-2xl font-bold md:text-3xl">{run.stages[0].label}</h2>
              <p className="mt-3 max-w-[42ch] text-[0.9375rem] leading-relaxed">{run.stages[0].description}</p>
            </div>
          </div>

          <div className="relative min-h-[420px] w-full overflow-hidden rounded-2xl border border-rule bg-ink p-8">
            <AnimatePresence>
              <motion.div
                key={activeStage}
                initial={{ opacity: 0, scale: 0.96 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.96 }}
                transition={{ duration: 0.45, ease: EASE }}
                className="absolute inset-0 flex items-center justify-center p-8"
              >
                <StageVisual
                  index={activeStage}
                  run={run}
                  persona={persona}
                  finding={finding}
                  local={localProgress}
                />
              </motion.div>
            </AnimatePresence>
          </div>
        </div>

        <RunningIndicator activeStage={activeStage} progress={fillProgress} stageCount={run.stages.length} />

        <p className="mt-6 font-mono text-[0.6875rem] uppercase tracking-wide text-ink-3">
          Task: {taskLabel} · Persona: {persona.name}
        </p>

        <Link
          to="/results"
          className="mt-8 inline-block font-mono text-[0.6875rem] uppercase tracking-wide text-ink-3 underline decoration-rule underline-offset-4 hover:text-ink hover:decoration-ink"
        >
          Skip to results →
        </Link>
      </main>
      <Footer />
    </>
  );
}

function RunningIndicator({
  activeStage,
  progress,
  stageCount,
}: {
  activeStage: number;
  progress: ReturnType<typeof useMotionValue<number>>;
  stageCount: number;
}) {
  return (
    <div className="mt-10 lg:mt-12">
      <div className="relative h-px w-full bg-rule">
        <motion.div style={{ scaleX: progress }} className="absolute inset-y-0 left-0 w-full origin-left bg-ink" />
      </div>
      <div className="mt-4 flex items-center justify-between">
        {Array.from({ length: stageCount }, (_, i) => (
          <span
            key={i}
            className={cn(
              "font-mono text-[0.6875rem] tabular-nums transition-colors duration-300",
              i === activeStage ? "text-ink" : i < activeStage ? "text-ink-3" : "text-ink-3/40",
            )}
          >
            {String(i + 1).padStart(2, "0")}
          </span>
        ))}
      </div>
    </div>
  );
}
