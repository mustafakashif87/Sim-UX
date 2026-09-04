import type { RefObject } from "react";
import { useReducedMotion, useScroll, useTransform } from "motion/react";
import type { Transition, Variants } from "motion/react";

/**
 * One easing curve for the whole product. Everything that moves here is a
 * machine part settling into place, so the curve decelerates hard and never
 * overshoots — no bounce, no spring wobble.
 */
export const EASE = [0.16, 1, 0.3, 1] as const;

export const transition = (duration = 0.6, delay = 0): Transition => ({
  duration,
  delay,
  ease: EASE,
});

/** Parent: holds children until it's in view, then releases them in sequence. */
export const containerVariants: Variants = {
  hidden: {},
  visible: {
    transition: { staggerChildren: 0.09, delayChildren: 0.06 },
  },
};

/** Slower release, for sections where each child is a substantial block. */
export const containerVariantsSlow: Variants = {
  hidden: {},
  visible: {
    transition: { staggerChildren: 0.14, delayChildren: 0.1 },
  },
};

/** Child: rises into position. */
export const itemVariants: Variants = {
  hidden: { opacity: 0, y: 20 },
  visible: { opacity: 1, y: 0, transition: transition(0.65) },
};

/** A hairline that draws itself left-to-right. Used for section rules. */
export const ruleVariants: Variants = {
  hidden: { scaleX: 0 },
  visible: { scaleX: 1, transition: { duration: 0.9, ease: EASE } },
};

/** Standard scroll trigger: fire once, a little before the block is centred. */
export const inView = { once: true, amount: 0.25 } as const;

/**
 * Drifts an element against the scroll while it crosses the viewport.
 *
 * Used to give the cards in a row slightly different rates, so the grid
 * breathes on the way past instead of moving as one slab. Keep `distance`
 * small — past about 40px it stops feeling like depth and starts feeling
 * like the layout is broken.
 */
export function useParallax(target: RefObject<HTMLElement>, distance = 24) {
  const reduce = useReducedMotion() ?? false;
  const { scrollYProgress } = useScroll({
    target,
    offset: ["start end", "end start"],
  });
  const y = useTransform(scrollYProgress, [0, 1], [distance, -distance]);
  return reduce ? undefined : y;
}
