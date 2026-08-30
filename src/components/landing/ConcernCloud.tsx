import { motion } from "motion/react";
import { SectionHeading } from "@/components/SectionHeading";
import { containerVariantsSlow, revealVariants, inViewTall, transition } from "@/lib/motion";

/**
 * M6b — replaces Wispr's dark "made for you" pill-tag section (Sales,
 * Consulting, Engineering...) plus its "Flow for Accessibility"
 * highlight card. Tags here are real accessibility/UX concern
 * categories; the highlighted card names SimUX's actual stakeholders
 * from the proposal, not an invented persona.
 *
 * M6c: tags settle in from a small per-tag rotation instead of a
 * uniform grid stagger (reads as a "cloud" settling, not a grid
 * snapping into place) — rotations are hand-picked/deterministic
 * (repeating pattern), not `Math.random()`, so the effect is
 * consistent across renders. The highlighted card now has a soft
 * radial glow behind it that finishes appearing before the card does
 * (shorter duration, same trigger point), like a spotlight landing
 * first.
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

// Deterministic, varied signs/magnitudes — not random, so re-renders
// (or a future SSR pass) stay consistent.
const TAG_ROTATIONS = [-3, 4, -2, 3, -4, 2, -3, 4];

export function ConcernCloud() {
  return (
    <section className="bg-ink py-20 md:py-28">
      <div className="container">
        <SectionHeading
          inverse
          eyebrow="Who this surfaces friction for"
          title="Real concerns, not a generic checklist."
        />

        <motion.div
          variants={containerVariantsSlow}
          initial="hidden"
          whileInView="visible"
          viewport={inViewTall}
          className="mt-10 flex flex-wrap gap-3"
        >
          {CONCERNS.map((concern, i) => (
            <motion.span
              key={concern}
              variants={{
                hidden: { opacity: 0, y: 16, rotate: TAG_ROTATIONS[i % TAG_ROTATIONS.length] },
                visible: { opacity: 1, y: 0, rotate: 0, transition: transition(0.5) },
              }}
              className="rounded-full border border-paper/20 px-4 py-2 font-mono text-xs text-paper/75"
            >
              {concern}
            </motion.span>
          ))}
        </motion.div>

        <div className="relative mt-10">
          <motion.div
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            viewport={inViewTall}
            transition={transition(0.4)}
            className="pointer-events-none absolute -inset-8 -z-10 rounded-full bg-[radial-gradient(closest-side,hsl(var(--persona-accessibility)/0.18),transparent)] blur-2xl"
            aria-hidden="true"
          />
          <motion.div
            variants={revealVariants}
            initial="hidden"
            whileInView="visible"
            viewport={inViewTall}
            className="rounded-2xl border border-paper/15 bg-paper/[0.04] p-6 md:p-8"
          >
            <p className="label-mono text-paper/50">Who this is for</p>
            <p className="mt-3 max-w-[62ch] text-[0.9375rem] leading-relaxed text-paper/75">
              Development and QA teams shipping the product, accessibility and compliance teams
              responsible for meeting standards like WCAG, and UX/accessibility audit agencies
              reviewing it for a client — the stakeholders this project's own proposal names, not a
              marketing wish list.
            </p>
          </motion.div>
        </div>
      </div>
    </section>
  );
}
