import { useState } from "react";
import { Link } from "react-router-dom";
import { motion } from "motion/react";
import { ArrowRight, Check } from "lucide-react";
import { SiteNav } from "@/components/SiteNav";
import { Footer } from "@/components/Footer";
import { Button } from "@/components/ui/button";
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
 * Mobile-first is genuinely selectable here, not inert — only its
 * "Phase 2 · FYP-II" badge marks it as not-yet-real, matching the same
 * correction already applied to PersonaShowcase's cards (dimming/
 * disabled-looking treatment was tried there and explicitly reversed).
 */

const TINT: Record<string, string> = {
  accessibility: "bg-persona-accessibility",
  motor: "bg-persona-motor",
  "mobile-first": "bg-persona-phase2",
};

export default function NewRun() {
  const run = useDemoRun();
  const [selected, setSelected] = useState<string[]>([]);
  const taskList = run.tasks.map((t) => t.label.toLowerCase()).join(" and ");

  return (
    <>
      <SiteNav variant="app" />
      <main className="container py-20 md:py-28">
        <motion.div initial="hidden" animate="visible" variants={containerVariantsSlow}>
          <motion.p variants={itemVariants} className="eyebrow-sans">
            New run
          </motion.p>
          <motion.h1 variants={itemVariants} className="mt-3 font-hero text-d1 text-ink">
            Choose who tests it.
          </motion.h1>
          <motion.p variants={itemVariants} className="mt-4 max-w-[58ch] text-ink-2">
            Each persona attempts {taskList} on {run.productName}, under its own restriction. Pick
            one or several — every run combines their findings into one ranked report.
          </motion.p>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={transition(0.6, 0.15)}
          className="mt-12"
        >
          <ToggleGroup
            type="multiple"
            value={selected}
            onValueChange={setSelected}
            className="grid gap-5 md:grid-cols-3"
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
          {selected.length > 0 ? (
            <Button asChild size="lg" className="group">
              <Link to="/running">
                Continue with {selected.length} {selected.length === 1 ? "persona" : "personas"}
                <ArrowRight className="h-4 w-4 transition-transform duration-200 group-hover:translate-x-0.5" />
              </Link>
            </Button>
          ) : (
            <Button size="lg" disabled>
              Select at least one persona
            </Button>
          )}
        </div>
      </main>
      <Footer />
    </>
  );
}

function PersonaSelectCard({ persona }: { persona: Persona }) {
  const isPlaceholder = persona.depth === "placeholder";

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
        {persona.id === "mobile-first" && (
          <div className="grid h-16 w-20 place-items-center rounded-md border border-dashed border-rule">
            <span className="font-mono text-[0.625rem] uppercase text-ink-3">preview</span>
          </div>
        )}
        {isPlaceholder && (
          <span className="rounded-full border border-persona-phase2-ink/30 bg-paper-raised px-2.5 py-1 font-mono text-[0.625rem] uppercase tracking-wide text-persona-phase2-ink">
            Phase 2 · FYP-II
          </span>
        )}
      </div>

      <h3 className="mt-5 font-display text-xl font-bold tracking-tight text-ink">{persona.name}</h3>
      <p className="mt-3 text-[0.9375rem] leading-relaxed text-ink-2">{persona.restriction}</p>
    </div>
  );
}
