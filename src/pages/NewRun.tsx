import { useState } from "react";
import { Link } from "react-router-dom";
import { motion } from "motion/react";
import { ArrowRight, Check } from "lucide-react";
import { SiteNav } from "@/components/SiteNav";
import { Footer } from "@/components/Footer";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group";
import { AccessibilityRestrictedView } from "@/components/personas/AccessibilityRestrictedView";
import { MotorImprecisePointer } from "@/components/personas/MotorImprecisePointer";
import { useDemoRun } from "@/hooks/useDemoRun";
import { cn } from "@/lib/utils";
import { containerVariantsSlow, itemVariants, transition } from "@/lib/motion";
import type { Persona } from "@/lib/types";

/**
 * M7 — real persona-selection screen, replacing the M4 placeholder.
 * Large soft-radius cards (not the checkbox-list metaphor Site Doctor
 * used for "pick checks to run" — see DESIGN.md §7), each embedding its
 * M5 at-rest restriction metaphor, reusing PersonaShowcase's exact
 * visual language so the landing page's showcase and this real
 * selection screen never look like two different products.
 *
 * Multi-select (`ToggleGroup type="multiple"`), not the milestone plan's
 * literal "radio-group" — a run tests "whichever personas you picked"
 * (plural; see PipelineStages' own copy and the Aggregate stage, which
 * already combines findings from two personas at once), so single-select
 * would contradict the product this is a POC of. Full reasoning in
 * CLAUDE.md §10.
 *
 * Mobile-first persona removed — was a Phase 2/FYP-II placeholder only,
 * never a working persona; only accessibility and motor are shown.
 *
 * Target-URL field: a plain text input above the persona grid, gating
 * Continue alongside persona selection. Purely a UI capture, per
 * POC_SPEC.md rule 1 — no fetch/crawl ever fires on it, and the fixture
 * run shown downstream is always Marlow's regardless of what's typed
 * here. Said explicitly in the helper text under the field rather than
 * left implicit, matching the honesty-disclaimer pattern already used
 * in Running.tsx/FindingDetail.tsx (never let a real-looking input
 * imply real execution without saying so right next to it).
 */

const TINT: Record<string, string> = {
  accessibility: "bg-persona-accessibility",
  motor: "bg-persona-motor",
};

export default function NewRun() {
  const run = useDemoRun();
  const [siteUrl, setSiteUrl] = useState("");
  const [selected, setSelected] = useState<string[]>([]);
  const taskList = run.tasks.map((t) => t.label.toLowerCase()).join(" and ");
  const canContinue = siteUrl.trim().length > 0 && selected.length > 0;

  return (
    <>
      <SiteNav variant="app" />
      <main className="container py-20 md:py-28">
        <motion.div initial="hidden" animate="visible" variants={containerVariantsSlow}>
          <motion.p variants={itemVariants} className="eyebrow-sans">
            New run
          </motion.p>
          <motion.h1 variants={itemVariants} className="mt-3 font-hero text-d1 text-ink">
            Choose what to test, and who tests it.
          </motion.h1>
          <motion.p variants={itemVariants} className="mt-4 max-w-[58ch] text-ink-2">
            Each persona attempts {taskList} on the site below, under its own restriction. Pick
            one or several — every run combines their findings into one ranked report.
          </motion.p>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={transition(0.6, 0.1)}
          className="mt-10 max-w-md"
        >
          <Label htmlFor="site-url">Website to audit</Label>
          <Input
            id="site-url"
            type="url"
            inputMode="url"
            placeholder="https://your-site.com"
            value={siteUrl}
            onChange={(e) => setSiteUrl(e.target.value)}
            className="mt-2"
          />
          <p className="mt-2 text-xs text-ink-3">
            This demo always walks through the same fixture case ({run.productName}'s{" "}
            {taskList}) — entering a URL here doesn't trigger a real audit.
          </p>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={transition(0.6, 0.15)}
          className="mt-10"
        >
          <ToggleGroup
            type="multiple"
            value={selected}
            onValueChange={setSelected}
            className="grid gap-5 md:grid-cols-2"
            aria-label="Select personas for this run"
          >
            {run.personas.map((persona) => (
              <ToggleGroupItem key={persona.id} value={persona.id} className="h-full">
                <PersonaSelectCard persona={persona} />
              </ToggleGroupItem>
            ))}
          </ToggleGroup>
        </motion.div>

        <div className="mt-10 flex flex-wrap items-center gap-4">
          {canContinue ? (
            <Button asChild size="lg" className="group">
              {/* Router `state` (not a query param or global store) is
                  deliberate: it's the smallest mechanism that actually
                  works here — Running.tsx (M8) needs to know which
                  personas/URL to narrate, nothing else in the app needs
                  this value, and it's gone the moment you navigate away
                  from `/running`, which is the correct lifetime for a
                  one-shot "what was picked for this run" handoff. */}
              <Link to="/running" state={{ personaIds: selected, siteUrl: siteUrl.trim() }}>
                Continue with {selected.length} {selected.length === 1 ? "persona" : "personas"}
                <ArrowRight className="h-4 w-4 transition-transform duration-200 group-hover:translate-x-0.5" />
              </Link>
            </Button>
          ) : (
            <Button size="lg" disabled>
              {siteUrl.trim().length === 0 ? "Enter a website to audit" : "Select at least one persona"}
            </Button>
          )}
        </div>
      </main>
      <Footer />
    </>
  );
}

function PersonaSelectCard({ persona }: { persona: Persona }) {
  return (
    <div
      className={cn(
        "card-chart-lg relative flex h-full flex-col p-6 transition-all duration-200",
        "group-hover:-translate-y-1 group-hover:shadow-lift",
        "group-data-[state=on]:translate-y-0 group-data-[state=on]:shadow-none",
        "group-data-[state=on]:ring-2 group-data-[state=on]:ring-ink group-data-[state=on]:ring-offset-2 group-data-[state=on]:ring-offset-paper",
        TINT[persona.id],
      )}
    >
      <span
        aria-hidden="true"
        className="absolute right-4 top-4 hidden h-6 w-6 place-items-center rounded-full bg-ink text-paper-raised group-data-[state=on]:grid"
      >
        <Check className="h-3.5 w-3.5" strokeWidth={3} />
      </span>

      <div className="flex items-center justify-between pr-8">
        {persona.id === "accessibility" && <AccessibilityRestrictedView size="thumbnail" active />}
        {persona.id === "motor" && <MotorImprecisePointer size="icon" active />}
      </div>

      <h3 className="mt-5 font-display text-xl font-bold tracking-tight text-ink">{persona.name}</h3>
      <p className="mt-3 text-[0.9375rem] leading-relaxed text-ink-2">{persona.restriction}</p>
    </div>
  );
}
