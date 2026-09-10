import { useRef } from "react";
import { motion, useInView } from "motion/react";
import { SectionHeading } from "@/components/SectionHeading";
import { AccessibilityRestrictedView } from "@/components/personas/AccessibilityRestrictedView";
import { MotorImprecisePointer } from "@/components/personas/MotorImprecisePointer";
import { useDemoRun } from "@/hooks/useDemoRun";
import { cn } from "@/lib/utils";
import { useParallax } from "@/lib/motion";

/**
 * Full rewrite of site-doctor's WhoItsFor.tsx: three audience cards
 * ("business owners" / "dev teams" / "solo developers") replaced with
 * the two actual personas (mobile-first removed — was a Phase 2/FYP-II
 * placeholder only, never a working persona). Section rhythm (card-per-column, per-card
 * scroll drift) is reused from the sibling; every word of content is
 * new. Cards use persona tint backgrounds, not the neutral stock
 * rotation — this section groups by persona, so per the M1/M2 rule the
 * two tinting systems never mix here.
 *
 * Scroll-triggered fade-in reveal (grid + per-card rise/scale/blur-in)
 * removed by request. Two scroll-linked effects are kept, since neither
 * is a fade-in: the per-card parallax drift (`useParallax`, a continuous
 * effect throughout scroll, not a one-time entrance), and each card's
 * restriction-simulation animation (blur/linearize, cursor miss-then-
 * correct) triggering once the card is actually on screen — that's the
 * persona-restriction demo itself, not decorative chrome.
 */

const TINT: Record<string, string> = {
  accessibility: "bg-persona-accessibility",
  motor: "bg-persona-motor",
};

const DRIFT = [18, 30];

export function PersonaShowcase() {
  const run = useDemoRun();
  const gridRef = useRef<HTMLDivElement>(null);

  return (
    <section id="personas" className="scroll-mt-24 border-t border-rule py-20 md:py-28">
      <div className="container">
        <SectionHeading
          eyebrow="Personas"
          title="Restricted on purpose, not roleplayed."
          lede="Each persona is a genuine perceptual or action limit, checkable in code — not an instruction telling a model to pretend. That difference is the whole point."
        />

        <div ref={gridRef} className="mt-14 grid gap-5 md:grid-cols-2" style={{ perspective: 1400 }}>
          {run.personas.map((persona, index) => (
            <PersonaCard key={persona.id} persona={persona} drift={DRIFT[index]} gridRef={gridRef} />
          ))}
        </div>
      </div>
    </section>
  );
}

function PersonaCard({
  persona,
  drift,
  gridRef,
}: {
  persona: ReturnType<typeof useDemoRun>["personas"][number];
  drift: number;
  gridRef: React.RefObject<HTMLDivElement>;
}) {
  const y = useParallax(gridRef, drift);
  // M6c: the restriction visuals used to render pre-blurred/static —
  // now they trigger for real once the card is actually on screen,
  // so the restriction demonstrates itself rather than being decoration.
  const cardRef = useRef<HTMLDivElement>(null);
  const cardInView = useInView(cardRef, { once: true, amount: 0.5 });

  return (
    <motion.div style={{ y }} className="group h-full">
      <div
        ref={cardRef}
        className={cn(
          "card-chart-lg flex h-full flex-col p-6 transition-all duration-300 hover:-translate-y-1 hover:shadow-lift",
          TINT[persona.id],
        )}
      >
        <div className="flex items-center justify-between">
          {persona.id === "accessibility" && (
            <AccessibilityRestrictedView size="thumbnail" active={cardInView} />
          )}
          {persona.id === "motor" && <MotorImprecisePointer size="icon" active={cardInView} />}
        </div>

        <h3 className="mt-5 font-display text-xl font-bold tracking-tight text-ink">
          {persona.name}
        </h3>
        <p className="mt-3 text-[0.9375rem] leading-relaxed text-ink-2">{persona.restriction}</p>
      </div>
    </motion.div>
  );
}
