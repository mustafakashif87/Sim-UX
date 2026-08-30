import type { CSSProperties } from "react";
import { motion, useReducedMotion } from "motion/react";
import { cn } from "@/lib/utils";
import { PageMockup } from "./PageMockup";

/**
 * The motor/age persona's actual restriction, made visible: full visual
 * access (no blur, unlike the accessibility persona), but pointer
 * actions are imprecise. The cursor below animates toward the promo
 * code area, lands on the input first (a miss — the real
 * motor-checkout-apply-button-size finding is that the Apply button is
 * ~18px and tightly packed against it), pauses, then corrects onto the
 * actual Apply button.
 *
 * Coordinates are percentages of an assumed ~280x210px rendered
 * PageMockup, estimated from its own layout rather than measured in a
 * browser (no browser tooling available this session) — treat as
 * approximate and adjust once actually seen.
 *
 * "icon" = compact form for the at-rest persona card (M7). "full" = the
 * larger form for the running state (M8).
 *
 * M6c: added `active` (defaults true — preserves "full"'s existing
 * always-looping behavior at every current call site). For "icon" size,
 * `active=false` (PersonaShowcase's initial state before the card
 * scrolls into view) shows the static "miss" position — the unresolved
 * problem, at rest; `active=true` loops the miss-then-correct sequence
 * continuously, same as "full" — an imprecise persona doesn't get it
 * right once and stop.
 */

const CURSOR = {
  start: { left: "10%", top: "15%" },
  miss: { left: "72%", top: "62%" }, // lands on the promo input, not Apply
  correct: { left: "91%", top: "62%" }, // corrects onto the actual Apply button
};

export function MotorImprecisePointer({
  size = "full",
  active = true,
  className,
}: {
  size?: "icon" | "full";
  active?: boolean;
  className?: string;
}) {
  const reduce = useReducedMotion() ?? false;

  if (size === "icon") {
    return (
      <div className={cn("relative h-16 w-20 overflow-hidden rounded-md border border-rule", className)} aria-hidden="true">
        <div className="scale-[0.29] origin-top-left">
          <PageMockup />
        </div>
        {!active ? (
          <Cursor style={{ left: CURSOR.miss.left, top: CURSOR.miss.top }} />
        ) : reduce ? (
          <Cursor style={{ left: CURSOR.correct.left, top: CURSOR.correct.top }} />
        ) : (
          // Always looping once active, matching the "full" size —
          // a persona that's imprecise doesn't get it right once and
          // stop, it keeps missing.
          <AnimatedCursor loop />
        )}
      </div>
    );
  }

  return (
    <div className={cn("relative inline-block", className)} aria-hidden="true">
      <PageMockup />
      {reduce || !active ? (
        // Reduced motion, or not yet active: show the end state only —
        // landed correctly, no miss, no animation.
        <Cursor style={{ left: CURSOR.correct.left, top: CURSOR.correct.top }} />
      ) : (
        <AnimatedCursor loop />
      )}
    </div>
  );
}

function AnimatedCursor({ loop }: { loop: boolean }) {
  return (
    <motion.div
      className="absolute z-10"
      initial={{ left: CURSOR.start.left, top: CURSOR.start.top, opacity: 0 }}
      animate={{
        left: [CURSOR.start.left, CURSOR.miss.left, CURSOR.miss.left, CURSOR.correct.left],
        top: [CURSOR.start.top, CURSOR.miss.top, CURSOR.miss.top, CURSOR.correct.top],
        opacity: [0, 1, 1, 1],
      }}
      transition={{
        duration: 2.2,
        times: [0, 0.45, 0.7, 1],
        ease: ["easeOut", "easeOut", "easeInOut"],
        ...(loop ? { repeat: Infinity, repeatDelay: 1 } : {}),
      }}
    >
      <CursorGlyph />
    </motion.div>
  );
}

function Cursor({ style }: { style: CSSProperties }) {
  return (
    <div className="absolute z-10" style={style}>
      <CursorGlyph />
    </div>
  );
}

function CursorGlyph() {
  return (
    <svg width="16" height="16" viewBox="0 0 16 16" className="-translate-x-1 -translate-y-1 drop-shadow-sm">
      <path d="M1 1l5.5 13 2-5.5L14 6.5z" fill="hsl(var(--ink))" stroke="hsl(var(--paper-raised))" strokeWidth="1" />
    </svg>
  );
}
