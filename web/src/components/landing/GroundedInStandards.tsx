/**
 * M6b — replaces Wispr's "Used by OpenAI/Replit/Amazon" customer-logo
 * strip. SimUX has no real users to name, so naming fabricated
 * customers was never an option; this names the two real sources its
 * citations actually come from instead (see fixtures/citations.ts).
 * Text wordmarks, not logo images — no rights to reproduce anyone's
 * actual logo, and text is more honest here than an implied-official
 * logo mark would be anyway.
 *
 * Scroll-triggered reveal (fade+rise on mount, delayed underline draw)
 * removed by request — names and underlines now render in place.
 */
const NAMES = ["W3C · WCAG 2.2", "Nielsen Norman Group"];

export function GroundedInStandards() {
  return (
    <section id="standards" className="scroll-mt-24 border-y border-paper/10 bg-ink py-10">
      <div className="container">
        <div className="flex flex-col items-center gap-6 sm:flex-row sm:justify-between">
          <p className="font-mono text-micro uppercase tracking-wide text-paper/50">
            Grounded in real standards
          </p>
          <div className="flex flex-wrap items-center justify-center gap-x-10 gap-y-3">
            {NAMES.map((name) => (
              <span key={name} className="relative inline-block pb-1.5">
                <span className="font-display text-lg font-bold tracking-tight text-paper/85">{name}</span>
                <span
                  className="absolute bottom-0 left-0 h-px w-full bg-paper/40"
                  aria-hidden="true"
                />
              </span>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
