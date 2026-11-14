import { useEffect, useRef, useState } from "react";
import { useReducedMotion } from "motion/react";

interface CountUpProps {
  to: number;
  duration?: number;
  delay?: number;
  /** Hold at 0 until told to run — lets a parent sequence several of these. */
  start?: boolean;
  className?: string;
}

/**
 * Counts a readout up to its value. Instruments settle on a number rather
 * than blinking to it. Ported as-is — fully generic, used for the UI Score
 * hero numeral (M9) and the severity-count tallies.
 */
export function CountUp({ to, duration = 900, delay = 0, start = true, className }: CountUpProps) {
  const reduce = useReducedMotion() ?? false;
  const [value, setValue] = useState(reduce ? to : 0);
  const frame = useRef<number>();

  useEffect(() => {
    if (reduce || !start) {
      setValue(reduce ? to : 0);
      return;
    }

    let startedAt: number | null = null;
    const tick = (now: number) => {
      if (startedAt === null) startedAt = now;
      const elapsed = now - startedAt - delay;
      if (elapsed < 0) {
        frame.current = requestAnimationFrame(tick);
        return;
      }
      const progress = Math.min(elapsed / duration, 1);
      // Same decelerating feel as the rest of the motion system.
      const eased = 1 - Math.pow(1 - progress, 3);
      setValue(Math.round(to * eased));
      if (progress < 1) frame.current = requestAnimationFrame(tick);
    };

    frame.current = requestAnimationFrame(tick);
    return () => {
      if (frame.current) cancelAnimationFrame(frame.current);
    };
  }, [to, duration, delay, start, reduce]);

  return (
    <span className={className} style={{ fontVariantNumeric: "tabular-nums" }}>
      {value}
    </span>
  );
}
