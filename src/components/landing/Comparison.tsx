import { motion } from "motion/react";
import { SectionHeading } from "@/components/SectionHeading";
import { containerVariantsSlow, itemVariants, inViewTall } from "@/lib/motion";

/**
 * M6b — replaces Wispr's "4x faster than typing / 220 WPM" stat-card
 * section. There is no real measured number to put here (nothing in
 * this POC runs), so this is a qualitative comparison instead, pulled
 * directly from the proposal's own Table 1.1 ("Ad hoc single-prompt LLM
 * critique" row) rather than an invented statistic dressed up to look
 * measured.
 *
 * M6c: the plain fade-in list rows are replaced with check/X marks that
 * draw themselves in (SVG `pathLength: 0 -> 1`, own `motion.path`/
 * `motion.line` rather than the lucide-react icon components, which
 * don't expose their internal path for this) — reads as each row being
 * actively marked, not just appearing.
 */

const CRITIQUE_POINTS = [
  "Persona is a roleplay instruction, not a real restriction",
  "One-shot opinion — nothing re-checks it",
  "Citations are model-recalled — can be wrong",
  "No fix verification of any kind",
];

const SIMUX_POINTS = [
  "Personas are genuine perceptual/action restrictions, checkable in code",
  "Real task attempts through actual interaction",
  "Every citation is retrieved from a real indexed source",
  "Every fix is sandboxed and re-verified before it's reported",
];

export function Comparison() {
  return (
    <section className="border-t border-rule py-20 md:py-28">
      <div className="container">
        <SectionHeading
          eyebrow="Why not just ask a chat model"
          title="The gap this closes."
          lede="Ad hoc single-prompt critique already exists — it's fast and free. It just doesn't hold up, per the same comparison this project's own proposal is built on."
        />

        <div className="mt-14 grid gap-6 md:grid-cols-2">
          <ComparisonColumn title="Single-prompt critique" points={CRITIQUE_POINTS} good={false} />
          <ComparisonColumn title="SimUX" points={SIMUX_POINTS} good />
        </div>
      </div>
    </section>
  );
}

function ComparisonColumn({
  title,
  points,
  good,
}: {
  title: string;
  points: string[];
  good: boolean;
}) {
  return (
    <div className={good ? "card-chart-lg bg-persona-accessibility p-6" : "card-chart-lg bg-paper-sunk p-6"}>
      <h3 className="font-display text-lg font-bold tracking-tight text-ink">{title}</h3>
      <motion.ul
        variants={containerVariantsSlow}
        initial="hidden"
        whileInView="visible"
        viewport={inViewTall}
        className="mt-4 space-y-3"
      >
        {points.map((point) => (
          <motion.li key={point} variants={itemVariants} className="flex items-start gap-2.5">
            {good ? <DrawnCheck /> : <DrawnX />}
            <span className="text-sm leading-relaxed text-ink-2">{point}</span>
          </motion.li>
        ))}
      </motion.ul>
    </div>
  );
}

function DrawnCheck() {
  return (
    <motion.svg
      viewBox="0 0 24 24"
      className="mt-0.5 h-4 w-4 shrink-0"
      fill="none"
      stroke="hsl(var(--minor-ink))"
      strokeWidth={2.5}
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <motion.path
        d="M20 6 9 17l-5-5"
        initial={{ pathLength: 0 }}
        whileInView={{ pathLength: 1 }}
        viewport={inViewTall}
        transition={{ duration: 0.45, ease: "easeOut" }}
      />
    </motion.svg>
  );
}

function DrawnX() {
  return (
    <motion.svg
      viewBox="0 0 24 24"
      className="mt-0.5 h-4 w-4 shrink-0"
      fill="none"
      stroke="hsl(var(--ink-3))"
      strokeWidth={2.5}
      strokeLinecap="round"
    >
      <motion.line
        x1="18" y1="6" x2="6" y2="18"
        initial={{ pathLength: 0 }}
        whileInView={{ pathLength: 1 }}
        viewport={inViewTall}
        transition={{ duration: 0.3, ease: "easeOut" }}
      />
      <motion.line
        x1="6" y1="6" x2="18" y2="18"
        initial={{ pathLength: 0 }}
        whileInView={{ pathLength: 1 }}
        viewport={inViewTall}
        transition={{ duration: 0.3, ease: "easeOut", delay: 0.2 }}
      />
    </motion.svg>
  );
}
