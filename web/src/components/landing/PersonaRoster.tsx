import { SectionHeading } from "@/components/SectionHeading";
import { PERSONA_ORDER, PERSONAS } from "@/lib/api";
import { cn } from "@/lib/utils";

/**
 * All fourteen personas, each named by the limit the harness enforces.
 * P1 to P3 are the fully evaluated core; P4 to P14 are the extension
 * (docs/persona-catalogue.md). Static: the same table New Run uses.
 */
export function PersonaRoster() {
  return (
    <section id="roster" className="scroll-mt-24 border-t border-rule py-20 md:py-28">
      <div className="container">
        <SectionHeading
          eyebrow="Fourteen personas"
          title="One limit each, enforced in code."
          lede="Three core personas are evaluated in full. Eleven more cover screen readers, keyboards, phones, zoom, skimming, interruptions, slow networks, help, habit, expert speed and older adults."
        />
        <ul className="mt-14 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {PERSONA_ORDER.map((id) => {
            const p = PERSONAS[id];
            return (
              <li
                key={id}
                className={cn(
                  "card-chart-lg flex h-full flex-col p-5",
                  p.core && "ring-2 ring-ink ring-offset-2 ring-offset-paper",
                )}
              >
                <p className="font-mono text-[0.75rem] uppercase tracking-wide text-ink-3">
                  {p.code} · {p.axis}
                  {p.core ? " · core" : ""}
                </p>
                <h3 className="mt-1 font-display text-lg font-bold tracking-tight text-ink">
                  {p.name}
                </h3>
                <p className="mt-2 text-[0.9375rem] leading-relaxed text-ink-2">{p.restriction}</p>
              </li>
            );
          })}
        </ul>
      </div>
    </section>
  );
}
