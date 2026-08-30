import { motion } from "motion/react";
import { containerVariants, itemVariants, inView, transition } from "@/lib/motion";

/**
 * M6b — replaces Wispr's "Used by OpenAI/Replit/Amazon" customer-logo
 * strip. SimUX has no real users to name, so naming fabricated
 * customers was never an option; this names the two real sources its
 * citations actually come from instead (see fixtures/citations.ts).
 * Text wordmarks, not logo images — no rights to reproduce anyone's
 * actual logo, and text is more honest here than an implied-official
 * logo mark would be anyway.
 *
 * M6c: each name now draws its own underline in *after* it appears
 * (a short delayed scaleX, not the generic fade every section had) —
 * reads as "this is being verified," not decoration, matching what the
 * strip is actually claiming.
 */
const NAMES = ["W3C · WCAG 2.2", "Nielsen Norman Group"];

export function GroundedInStandards() {
  return (
    <section id="standards" className="scroll-mt-24 border-y border-paper/10 bg-ink py-10">
      <div className="container">
        <motion.div
          variants={containerVariants}
          initial="hidden"
          whileInView="visible"
          viewport={inView}
          className="flex flex-col items-center gap-6 sm:flex-row sm:justify-between"
        >
          <motion.p variants={itemVariants} className="font-mono text-micro uppercase tracking-wide text-paper/50">
            Grounded in real standards
          </motion.p>
          <motion.div variants={itemVariants} className="flex flex-wrap items-center justify-center gap-x-10 gap-y-3">
            {NAMES.map((name, i) => (
              <span key={name} className="relative inline-block pb-1.5">
                <span className="font-display text-lg font-bold tracking-tight text-paper/85">{name}</span>
                <motion.span
                  initial={{ scaleX: 0 }}
                  whileInView={{ scaleX: 1 }}
                  viewport={inView}
                  transition={transition(0.5, 0.5 + i * 0.2)}
                  className="absolute bottom-0 left-0 h-px w-full origin-left bg-paper/40"
                  aria-hidden="true"
                />
              </span>
            ))}
          </motion.div>
        </motion.div>
      </div>
    </section>
  );
}
