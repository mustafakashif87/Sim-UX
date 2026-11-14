import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { motion } from "motion/react";
import { ArrowRight, TrendingUp } from "lucide-react";
import { SiteNav } from "@/components/SiteNav";
import { Footer } from "@/components/Footer";
import { SeverityTag } from "@/components/SeverityTag";
import { CountUp } from "@/components/CountUp";
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group";
import { useDemoRun } from "@/hooks/useDemoRun";
import { cn } from "@/lib/utils";
import { transition } from "@/lib/motion";
import type { DemoRun, Finding, Severity } from "@/lib/types";

/**
 * M9 — the real results/aggregation dashboard, replacing the M4
 * placeholder (a bare title + flat findings list).
 *
 * Shows the full fixture "run" regardless of which personas were
 * selected in M7/M8 — that selection drove the Running-screen
 * narration (M8's own scope), not what data this dashboard displays.
 * `useDemoRun()`'s fixture is one fixed completed run; persona here is
 * a FILTER on that fixed report, not a "only show what was actually
 * run" restriction — matching how the milestone's own spec frames it
 * ("persona as a first-class grouping/filter alongside severity"),
 * and avoiding inventing a reason to thread run-selection state through
 * the router a second time when nothing here needs it.
 *
 * Severity-grouped findings stay the primary structure (findings are
 * always grouped by severity); the persona filter narrows within that
 * structure rather than replacing it — satisfies "persona filter
 * toggling changes visible cards while severity grouping stays intact."
 */

const SEVERITY_ORDER: Severity[] = ["high", "medium", "low"];
const SEVERITY_GROUP_LABEL: Record<Severity, string> = { high: "High", medium: "Medium", low: "Low" };

const PERSONA_BADGE: Record<string, string> = {
  accessibility: "bg-persona-accessibility text-[hsl(var(--persona-accessibility-ink))]",
  motor: "bg-persona-motor text-[hsl(var(--persona-motor-ink))]",
};

export default function Results() {
  const run = useDemoRun();
  const [severityFilter, setSeverityFilter] = useState("all");
  const [personaFilter, setPersonaFilter] = useState("all");

  // Only personas that actually have findings get a filter option —
  // derived rather than hardcoded so this stays correct if the fixture
  // ever adds a persona with no findings yet.
  const personaOptions = useMemo(
    () => run.personas.filter((p) => run.findings.some((f) => f.personaId === p.id)),
    [run.personas, run.findings],
  );

  const filtered = useMemo(
    () =>
      run.findings.filter((f) => {
        if (severityFilter !== "all" && f.severity !== severityFilter) return false;
        if (personaFilter !== "all" && f.personaId !== personaFilter) return false;
        return true;
      }),
    [run.findings, severityFilter, personaFilter],
  );

  const grouped = useMemo(() => {
    const groups: Record<Severity, Finding[]> = { high: [], medium: [], low: [] };
    filtered.forEach((f) => groups[f.severity].push(f));
    return groups;
  }, [filtered]);

  return (
    <>
      <SiteNav variant="app" />
      <main className="container py-20 md:py-28">
        <p className="eyebrow-sans">Results</p>
        <h1 className="mt-3 font-hero text-d1 text-ink">{run.productName} — audit report.</h1>
        <p className="mt-4 max-w-[58ch] text-ink-2">
          Findings from every persona in this run, combined into one ranked report. Nothing here reflects a
          live computation — this is a completed, scripted example run.
        </p>

        <ScoreHero run={run} />

        <div className="mt-14 flex flex-wrap items-center gap-x-8 gap-y-4">
          <FilterGroup
            label="Severity"
            value={severityFilter}
            onChange={setSeverityFilter}
            options={[
              { value: "all", label: "All" },
              { value: "high", label: "High" },
              { value: "medium", label: "Medium" },
              { value: "low", label: "Low" },
            ]}
          />
          <FilterGroup
            label="Persona"
            value={personaFilter}
            onChange={setPersonaFilter}
            options={[{ value: "all", label: "All" }, ...personaOptions.map((p) => ({ value: p.id, label: p.name }))]}
          />
        </div>

        <div className="mt-8 space-y-12">
          {filtered.length === 0 && (
            <p className="rounded-lg border border-dashed border-rule bg-paper-sunk p-8 text-center text-sm text-ink-3">
              No findings match these filters.
            </p>
          )}
          {SEVERITY_ORDER.map(
            (sev) =>
              grouped[sev].length > 0 && (
                <section key={sev}>
                  <div className="flex items-center gap-3">
                    <SeverityTag severity={sev} variant="outline" />
                    <h2 className="font-display text-lg font-bold tracking-tight text-ink">
                      {SEVERITY_GROUP_LABEL[sev]}
                    </h2>
                    <span className="font-mono text-xs text-ink-3">{grouped[sev].length}</span>
                  </div>
                  <ul className="mt-4 space-y-3">
                    {grouped[sev].map((f) => (
                      <FindingCard key={f.id} finding={f} run={run} />
                    ))}
                  </ul>
                </section>
              ),
          )}
        </div>

        <RunHistory run={run} />
      </main>
      <Footer />
    </>
  );
}

function ScoreHero({ run }: { run: DemoRun }) {
  return (
    <div className="mt-12 grid gap-8 rounded-2xl border border-rule bg-paper-raised p-8 md:grid-cols-[auto_1fr] md:items-center md:gap-14">
      <div>
        <p className="label-mono">UI Score</p>
        <p className="mt-2 font-hero text-7xl font-bold text-ink">
          <CountUp to={run.uiScore.composite} />
        </p>
      </div>
      <div className="grid gap-6 border-t border-rule pt-6 sm:grid-cols-2 md:border-l md:border-t-0 md:pl-14 md:pt-0">
        <ScoreBreakdown label="Visual design" value={run.uiScore.visualDesign} delay={0.1} />
        <ScoreBreakdown label="Accessibility-visual" value={run.uiScore.accessibilityVisual} delay={0.25} />
      </div>
    </div>
  );
}

function ScoreBreakdown({ label, value, delay }: { label: string; value: number; delay: number }) {
  return (
    <div>
      <p className="font-mono text-[0.625rem] uppercase tracking-wide text-ink-3">{label}</p>
      <div className="mt-2 flex items-center gap-3">
        <p className="font-display text-xl font-bold text-ink">
          <CountUp to={value} delay={delay * 1000} />
        </p>
        <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-paper-sunk">
          <motion.div
            initial={{ scaleX: 0 }}
            animate={{ scaleX: value / 100 }}
            transition={transition(0.8, delay)}
            className="h-full origin-left rounded-full bg-ink"
          />
        </div>
      </div>
    </div>
  );
}

function FilterGroup({
  label,
  value,
  onChange,
  options,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  options: { value: string; label: string }[];
}) {
  return (
    <div className="flex flex-wrap items-center gap-2.5">
      <span className="font-mono text-[0.625rem] uppercase tracking-wide text-ink-3">{label}</span>
      <ToggleGroup
        type="single"
        value={value}
        onValueChange={(v) => v && onChange(v)}
        className="flex flex-wrap gap-1.5"
        aria-label={`Filter by ${label.toLowerCase()}`}
      >
        {options.map((opt) => (
          <ToggleGroupItem key={opt.value} value={opt.value} className="w-auto">
            <span className="inline-flex items-center rounded-full border border-rule px-3 py-1.5 font-mono text-[0.6875rem] uppercase tracking-wide text-ink-2 transition-colors group-data-[state=on]:border-ink group-data-[state=on]:bg-ink group-data-[state=on]:text-paper-raised">
              {opt.label}
            </span>
          </ToggleGroupItem>
        ))}
      </ToggleGroup>
    </div>
  );
}

function FindingCard({ finding, run }: { finding: Finding; run: DemoRun }) {
  const persona = run.personas.find((p) => p.id === finding.personaId)!;
  return (
    <li>
      <Link
        to={`/results/${finding.id}`}
        className="group flex items-start gap-4 rounded-lg border border-rule bg-paper-raised p-5 transition-all duration-200 hover:-translate-y-0.5 hover:shadow-lift"
      >
        <SeverityTag severity={finding.severity} className="mt-0.5 shrink-0" />
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <span
              className={cn(
                "rounded-full px-2 py-0.5 font-mono text-[0.625rem] uppercase tracking-wide",
                PERSONA_BADGE[persona.id],
              )}
            >
              {persona.name}
            </span>
            {finding.showcase && (
              <span className="rounded-full border border-[hsl(var(--minor))]/35 bg-[hsl(var(--minor))]/10 px-2 py-0.5 font-mono text-[0.625rem] uppercase tracking-wide text-[hsl(var(--minor-ink))]">
                Showcase
              </span>
            )}
          </div>
          <p className="mt-2 font-display text-base font-semibold text-ink group-hover:underline">
            {finding.title}
          </p>
          <p className="mt-1.5 line-clamp-2 text-sm text-ink-2">{finding.observation}</p>
        </div>
        <ArrowRight className="mt-1 h-4 w-4 shrink-0 text-ink-3 transition-transform duration-200 group-hover:translate-x-0.5" />
      </Link>
    </li>
  );
}

function RunHistory({ run }: { run: DemoRun }) {
  const currentCounts = {
    high: run.findings.filter((f) => f.severity === "high").length,
    medium: run.findings.filter((f) => f.severity === "medium").length,
    low: run.findings.filter((f) => f.severity === "low").length,
  };

  // Most-recent-first in fixture data; reversed here so the bar chart
  // reads left-to-right oldest -> newest, ending on the current run.
  const rows = [
    ...[...run.history].reverse().map((h) => ({
      key: h.id,
      dateLabel: formatShortDate(h.ranAt),
      uiScore: h.uiScore,
      current: false,
    })),
    { key: "current", dateLabel: "Current", uiScore: run.uiScore.composite, current: true },
  ];
  const maxScore = Math.max(...rows.map((r) => r.uiScore), 1);

  return (
    <section className="mt-20 border-t border-rule pt-14">
      <p className="eyebrow-sans">Run history</p>
      <h2 className="mt-3 font-display text-2xl font-bold tracking-tight text-ink">Regression, tracked.</h2>
      <p className="mt-3 max-w-[54ch] text-ink-2">
        Every run is compared against the ones before it, so a report shows whether things are actually
        getting better, not just what's wrong today.
      </p>

      <div className="mt-10 flex items-end gap-8">
        <div className="flex items-end gap-6">
          {rows.map((row, i) => (
            <div key={row.key} className="flex flex-col items-center gap-2.5">
              <div className="flex h-32 items-end">
                <motion.div
                  initial={{ height: 0 }}
                  animate={{ height: `${Math.max(12, (row.uiScore / maxScore) * 100)}%` }}
                  transition={transition(0.7, i * 0.08)}
                  className={cn("w-11 rounded-t-sm", row.current ? "bg-ink" : "bg-ink/25")}
                />
              </div>
              <span className={cn("font-mono text-xs tabular-nums", row.current ? "text-ink" : "text-ink-3")}>
                {row.uiScore}
              </span>
              <span className="font-mono text-[0.5625rem] uppercase tracking-wide text-ink-3">
                {row.dateLabel}
              </span>
            </div>
          ))}
        </div>
        <TrendingUp className="mb-9 h-5 w-5 shrink-0 text-[hsl(var(--minor))]" aria-hidden="true" />
      </div>

      <p className="mt-8 font-mono text-[0.6875rem] uppercase tracking-wide text-ink-3">
        Current run — {currentCounts.high} high · {currentCounts.medium} medium · {currentCounts.low} low
      </p>
    </section>
  );
}

function formatShortDate(iso: string) {
  return new Date(iso).toLocaleDateString(undefined, { month: "short", day: "numeric" });
}
