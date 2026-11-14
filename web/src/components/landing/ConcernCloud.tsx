import { SectionHeading } from "@/components/SectionHeading";

/**
 * M6b — replaces Wispr's dark "made for you" pill-tag section (Sales,
 * Consulting, Engineering...) plus its "Flow for Accessibility"
 * highlight card. Tags here are real accessibility/UX concern
 * categories; the highlighted card names SimUX's actual stakeholders
 * from the proposal, not an invented persona.
 *
 * Scroll-triggered reveal (per-tag settle-in, spotlight fade, card
 * rise-in) removed by request — the cloud and highlight card now render
 * in their final state immediately.
 */

const CONCERNS = [
  "Screen reader users",
  "Motor impairment",
  "Low vision",
  "Keyboard-only navigation",
  "Cognitive load",
  "Situational limits",
  "Aging users",
  "One-handed use",
];

export function ConcernCloud() {
  return (
    <section className="bg-ink py-20 md:py-28">
      <div className="container">
        <SectionHeading
          inverse
          eyebrow="Who this surfaces friction for"
          title="Real concerns, not a generic checklist."
        />

        <div className="mt-10 flex flex-wrap gap-3">
          {CONCERNS.map((concern) => (
            <span
              key={concern}
              className="rounded-full border border-paper/20 px-4 py-2 font-mono text-xs text-paper/75"
            >
              {concern}
            </span>
          ))}
        </div>

        <div className="relative mt-10">
          <div
            className="pointer-events-none absolute -inset-8 -z-10 rounded-full bg-[radial-gradient(closest-side,hsl(var(--persona-accessibility)/0.18),transparent)] blur-2xl"
            aria-hidden="true"
          />
          <div className="rounded-2xl border border-paper/15 bg-paper/[0.04] p-6 md:p-8">
            <p className="label-mono text-paper/50">Who this is for</p>
            <p className="mt-3 max-w-[62ch] text-[0.9375rem] leading-relaxed text-paper/75">
              Development and QA teams shipping the product, accessibility and compliance teams
              responsible for meeting standards like WCAG, and UX/accessibility audit agencies
              reviewing it for a client — the stakeholders this project's own proposal names, not a
              marketing wish list.
            </p>
          </div>
        </div>
      </div>
    </section>
  );
}
