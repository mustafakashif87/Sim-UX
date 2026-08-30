import { motion } from "motion/react";
import { cn } from "@/lib/utils";
import {
  containerVariants,
  itemVariants,
  ruleVariants,
  wordContainerVariants,
  wordVariants,
  inView,
} from "@/lib/motion";

interface SectionHeadingProps {
  eyebrow: string;
  title: string;
  lede?: string;
  inverse?: boolean;
  className?: string;
}

/**
 * Ported from site-doctor with one deliberate change: the eyebrow now uses
 * `.eyebrow-sans` (sentence-case tracked sans, per DESIGN.md) instead of
 * `.label-mono` (uppercase mono). This is exactly the "editorial section
 * label" case the M1 convention comment calls out as NOT genuinely
 * code-like content — the old site-doctor default of reaching for
 * label-mono here was habit, not a deliberate choice.
 */
export function SectionHeading({
  eyebrow,
  title,
  lede,
  inverse = false,
  className,
}: SectionHeadingProps) {
  const words = title.split(" ");

  return (
    <motion.div
      variants={containerVariants}
      initial="hidden"
      whileInView="visible"
      viewport={inView}
      className={cn("max-w-3xl", className)}
    >
      <motion.p variants={itemVariants} className={cn("eyebrow-sans", inverse && "text-paper/65")}>
        {eyebrow}
      </motion.p>

      <motion.div
        variants={ruleVariants}
        className={cn("my-4 h-px origin-left", inverse ? "bg-paper/25" : "bg-rule")}
      />

      {/* The title reads itself into place a word at a time. Each word gets
          its own clipping wrapper so it rises out of the line rather than
          sliding across whatever sits above it.

          pb-[0.2em] (was 0.08em): tuned up after switching font-hero to
          Instrument Serif — its display metrics leave less headroom
          below the baseline than the previous font did, and a word with
          a descender (e.g. "roleplayed.") could clip against the old,
          tighter padding right as it settled into final position,
          reading as a small glitch at the end of the reveal. Best-guess
          fix, not confirmed visually (no browser this session) — flag
          if it's still off. */}
      <motion.h2
        variants={wordContainerVariants}
        className={cn("text-d2 font-hero", inverse && "text-paper")}
      >
        {words.map((word, index) => (
          <span
            key={`${word}-${index}`}
            className="inline-block overflow-hidden pb-[0.2em] align-bottom"
          >
            <motion.span variants={wordVariants} className="inline-block">
              {word}
              {index < words.length - 1 && " "}
            </motion.span>
          </span>
        ))}
      </motion.h2>

      {lede && (
        <motion.p
          variants={itemVariants}
          className={cn(
            "mt-5 max-w-[62ch] text-lg leading-relaxed",
            inverse ? "text-paper/70" : "text-ink-2",
          )}
        >
          {lede}
        </motion.p>
      )}
    </motion.div>
  );
}
