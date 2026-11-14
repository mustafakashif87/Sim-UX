import { cn } from "@/lib/utils";

/**
 * A fake "screenshot" of Marlow's checkout page — built from real markup
 * (divs styled to look like a checkout UI), not a captured image, since
 * nothing in this POC ever actually crawls or screenshots a real site
 * (POC_SPEC.md rule 2). Deliberately built to embody the exact findings
 * from fixtures/demoRun.ts, not an arbitrary mockup:
 *
 * - The "Apply" button next to the promo field is genuinely tiny and
 *   tight against its neighbor (motor-checkout-apply-button-size).
 * - The quantity stepper's minus button sits close enough to the input
 *   to plausibly misregister (motor-checkout-stepper-overlap).
 * - The "Continue" button has an icon only, no visible text (this is
 *   what makes it a plausible target for the accessibility persona's
 *   "no accessible name" finding — a11y-checkout-continue-button).
 *
 * Fixed natural size (280px wide) — callers scale it via a wrapping
 * container/transform rather than this component taking a size prop,
 * so the internal layout never has to reflow.
 */
export function PageMockup({ className }: { className?: string }) {
  return (
    <div
      className={cn("w-[280px] overflow-hidden rounded-md border border-rule bg-paper-raised", className)}
      aria-hidden="true"
    >
      {/* Top bar */}
      <div className="flex items-center justify-between bg-ink px-3 py-2">
        <span className="font-display text-xs font-bold tracking-tight text-paper">Marlow</span>
        <span className="h-3 w-3 rounded-full bg-paper/40" />
      </div>

      <div className="space-y-4 p-4">
        {/* Product row */}
        <div className="flex items-center gap-3">
          <div className="h-12 w-12 shrink-0 rounded-sm bg-paper-sunk" />
          <div className="min-w-0 flex-1 space-y-1.5">
            <div className="h-2 w-3/4 rounded-full bg-ink/25" />
            <div className="h-2 w-1/3 rounded-full bg-ink/15" />
          </div>
          {/* Quantity stepper — minus button sits tight against the input. */}
          <div className="flex items-center overflow-hidden rounded-sm border border-rule">
            <span className="grid h-5 w-5 place-items-center bg-paper-sunk text-[10px] leading-none text-ink-2">
              −
            </span>
            <span className="grid h-5 w-6 place-items-center bg-paper-raised text-[10px] leading-none text-ink">
              1
            </span>
            <span className="grid h-5 w-5 place-items-center bg-paper-sunk text-[10px] leading-none text-ink-2">
              +
            </span>
          </div>
        </div>

        {/* Promo code row — Apply button is deliberately ~18px, tight spacing. */}
        <div className="flex items-center gap-1">
          <div className="h-6 flex-1 rounded-sm border border-rule bg-paper-sunk px-2">
            <div className="mt-[7px] h-1.5 w-1/2 rounded-full bg-ink/15" />
          </div>
          <span className="grid h-[18px] w-[18px] shrink-0 place-items-center rounded-[3px] bg-ink text-[8px] font-bold leading-none text-paper">
            OK
          </span>
        </div>

        {/* Continue button — icon only, no visible text (the actual bug). */}
        <div className="flex h-9 items-center justify-center rounded-md bg-ink">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" aria-hidden="true">
            <path
              d="M5 12h14M13 6l6 6-6 6"
              stroke="hsl(var(--paper-raised))"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
        </div>
      </div>
    </div>
  );
}
