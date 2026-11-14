import { useState } from "react";
import { Link, useParams } from "react-router-dom";
import { AnimatePresence, motion } from "motion/react";
import { ArrowLeft, ArrowRight, Quote } from "lucide-react";
import { SiteNav } from "@/components/SiteNav";
import { Footer } from "@/components/Footer";
import { Button } from "@/components/ui/button";
import { SeverityTag } from "@/components/SeverityTag";
import { FixVisual, SandboxVisual, VerifyVisual } from "@/components/landing/PipelineStages";
import { useDemoRun } from "@/hooks/useDemoRun";
import { cn } from "@/lib/utils";
import { EASE } from "@/lib/motion";
import type { Citation, Finding, Persona } from "@/lib/types";

/**
 * M10 — the real finding-detail screen, replacing the M4 placeholder.
 *
 * Only the two showcase findings (`finding.showcase` present — one per
 * full-depth persona, POC_SPEC.md §6 item 5) get the interactive
 * fix -> sandbox -> verify walkthrough. Every other finding renders as
 * a plain recap (observation, recommendation, citation if any) with an
 * explicit, honest note that there's no walkthrough for it — not a
 * silently thinner version of the same UI.
 *
 * The walkthrough reuses `FixVisual`/`SandboxVisual`/`VerifyVisual`
 * directly from PipelineStages.tsx (exported for exactly this reuse)
 * rather than rebuilding the same three panels a third time — so the
 * landing-page preview, the Running-screen narration (M8), and this
 * actual click-through walkthrough all show the same visual language
 * for the same three steps.
 *
 * Advances only on user action (Next/Back buttons) — never auto-plays.
 * POC_SPEC.md §7's guardrail is specifically about not implying live
 * execution; a user-paced wizard is the opposite of that.
 */

const STEPS = [
  { id: "fix", label: "Propose fix" },
  { id: "sandbox", label: "Sandbox" },
  { id: "verify", label: "Verify" },
] as const;

const PERSONA_BADGE: Record<string, string> = {
  accessibility: "bg-persona-accessibility text-[hsl(var(--persona-accessibility-ink))]",
  motor: "bg-persona-motor text-[hsl(var(--persona-motor-ink))]",
};

export default function FindingDetail() {
  const { findingId } = useParams<{ findingId: string }>();
  const run = useDemoRun();
  const finding = run.findings.find((f) => f.id === findingId);

  if (!finding) {
    return (
      <>
        <SiteNav variant="app" />
        <main className="container py-20 md:py-28">
          <BackLink />
          <h1 className="mt-6 font-hero text-d1 text-ink">Not found.</h1>
          <p className="mt-4 text-ink-2">No finding matches id &ldquo;{findingId}&rdquo;.</p>
        </main>
        <Footer />
      </>
    );
  }

  const persona = run.personas.find((p) => p.id === finding.personaId)!;

  return (
    <>
      <SiteNav variant="app" />
      <main className="container py-20 md:py-28">
        <BackLink />

        <div className="mt-6 flex flex-wrap items-center gap-2.5">
          <SeverityTag severity={finding.severity} />
          <span
            className={cn(
              "rounded-full px-2.5 py-1 font-mono text-[0.6875rem] uppercase tracking-wide",
              PERSONA_BADGE[persona.id],
            )}
          >
            {persona.name}
          </span>
        </div>
        <h1 className="mt-4 max-w-[42ch] font-hero text-d1 text-ink">{finding.title}</h1>

        <div className="mt-10 grid gap-12 lg:grid-cols-2 lg:gap-16">
          <div>
            <Section label="What SimUX observed">{finding.observation}</Section>
            <Section label="Recommendation">{finding.recommendation}</Section>
            {finding.citation && (
              <div className="border-t border-rule py-6">
                <p className="font-mono text-[0.625rem] uppercase tracking-wide text-ink-3">Grounded in</p>
                <CitationCard citation={finding.citation} />
              </div>
            )}
          </div>

          <div>
            {finding.showcase ? (
              <Walkthrough persona={persona} finding={finding} />
            ) : (
              <div className="rounded-2xl border border-dashed border-rule bg-paper-sunk p-8 text-center">
                <p className="text-sm leading-relaxed text-ink-3">
                  No fix walkthrough for this finding — only the two showcase findings (one per
                  full-depth persona) get the full propose → sandbox → verify demo. Every other
                  finding, including this one, stays a plain triaged card.
                </p>
              </div>
            )}
          </div>
        </div>
      </main>
      <Footer />
    </>
  );
}

function BackLink() {
  return (
    <Link
      to="/results"
      className="inline-flex items-center gap-1.5 font-mono text-[0.6875rem] uppercase tracking-wide text-ink-3 transition-colors hover:text-ink"
    >
      <ArrowLeft className="h-3.5 w-3.5" />
      Back to results
    </Link>
  );
}

function Section({ label, children }: { label: string; children: string }) {
  return (
    <div className="border-t border-rule py-6 first:border-t-0 first:pt-0">
      <p className="font-mono text-[0.625rem] uppercase tracking-wide text-ink-3">{label}</p>
      <p className="mt-2 text-[0.9375rem] leading-relaxed text-ink-2">{children}</p>
    </div>
  );
}

function CitationCard({ citation }: { citation: Citation }) {
  return (
    <div className="mt-2 rounded-lg border border-rule bg-paper-raised p-5">
      <Quote className="h-4 w-4 text-ink-3/50" strokeWidth={1.5} />
      <p className="mt-2 font-body text-sm italic leading-relaxed text-ink">&ldquo;{citation.text}&rdquo;</p>
      <div className="mt-4 flex items-center justify-between border-t border-rule pt-3">
        <span className="font-mono text-[0.625rem] uppercase tracking-wide text-ink-3">{citation.id}</span>
        <span className="rounded-full bg-minor/15 px-2 py-0.5 font-mono text-[0.625rem] uppercase text-[hsl(var(--minor-ink))]">
          Verified
        </span>
      </div>
    </div>
  );
}

function Walkthrough({ persona, finding }: { persona: Persona; finding: Finding }) {
  const [step, setStep] = useState(0);
  const isLast = step === STEPS.length - 1;

  return (
    <div>
      <p className="mb-3 font-mono text-[0.6875rem] uppercase tracking-wide text-ink-3">
        A scripted walkthrough, advanced by you — not a live fix applied and re-verified in real time.
      </p>
      <div className="relative min-h-[420px] overflow-hidden rounded-2xl border border-rule bg-ink p-8">
        <AnimatePresence>
          <motion.div
            key={step}
            initial={{ opacity: 0, x: 24 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -24 }}
            transition={{ duration: 0.4, ease: EASE }}
            className="absolute inset-0 flex items-center justify-center p-8"
          >
            {step === 0 && <FixVisual finding={finding} />}
            {step === 1 && <SandboxVisual />}
            {step === 2 && <VerifyVisual persona={persona} finding={finding} />}
          </motion.div>
        </AnimatePresence>
      </div>

      <ol className="mt-6 flex flex-wrap items-center gap-2">
        {STEPS.map((s, i) => (
          <li key={s.id} className="flex items-center gap-2">
            <span
              className={cn(
                "grid h-6 w-6 place-items-center rounded-full font-mono text-[0.625rem] transition-colors duration-300",
                i === step ? "bg-ink text-paper-raised" : i < step ? "bg-ink/15 text-ink" : "bg-paper-sunk text-ink-3",
              )}
            >
              {i + 1}
            </span>
            <span
              className={cn(
                "font-mono text-[0.6875rem] uppercase tracking-wide transition-colors duration-300",
                i === step ? "text-ink" : "text-ink-3",
              )}
            >
              {s.label}
            </span>
            {i < STEPS.length - 1 && <span className="mx-1 h-px w-6 bg-rule" aria-hidden="true" />}
          </li>
        ))}
      </ol>

      <div className="mt-6 flex items-center gap-3">
        <Button variant="outline" onClick={() => setStep((s) => Math.max(0, s - 1))} disabled={step === 0}>
          <ArrowLeft className="h-4 w-4" />
          Back
        </Button>
        {isLast ? (
          <Button asChild>
            <Link to="/results">Back to results</Link>
          </Button>
        ) : (
          <Button onClick={() => setStep((s) => Math.min(STEPS.length - 1, s + 1))}>
            Next
            <ArrowRight className="h-4 w-4" />
          </Button>
        )}
      </div>
    </div>
  );
}
