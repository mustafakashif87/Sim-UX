import { cn } from "@/lib/utils";
import { PageMockup } from "./PageMockup";

/**
 * The accessibility persona's actual restriction, made visible: it never
 * receives the screenshot, layout, or CSS — only a linearized
 * accessibility-tree reading order. The blur/desaturate on the left is a
 * visual metaphor for "this agent cannot see this"; the plain list on
 * the right is what it perceives instead. The list's last two rows are
 * deliberately identical in shape to demonstrate the actual finding
 * (a11y-checkout-continue-button) — a button that reads as nothing more
 * than "button."
 *
 * "thumbnail" = small, no text list — for the at-rest persona card (M7).
 * "full" = both panels, larger — for the running state (M8) and Hero's
 * toggle.
 *
 * M6c: added `active` (defaults true — preserves every existing call
 * site's always-blurred behavior unchanged). PersonaShowcase is the one
 * caller that passes `active={false}` initially and flips it true once
 * the card scrolls into view, so the blur genuinely transitions in
 * instead of being pre-rendered in its end state.
 */

// Exported so PipelineStages.tsx's narrower Persona-attempts stage can
// build its own single-column layout from the same list — the "full"
// variant's 2-column grid below needs ~500px+ (280px mockup + a
// readable list column) and doesn't fit that stage's ~460px column.
export const READING_ORDER = [
  "Marlow",
  "Product: quantity input",
  "Decrease quantity, button",
  "Increase quantity, button",
  "Promo code, edit text",
  "OK, button",
  "button", // <- a11y-checkout-continue-button: no accessible name
];

export function AccessibilityRestrictedView({
  size = "full",
  active = true,
  className,
}: {
  size?: "thumbnail" | "full";
  active?: boolean;
  className?: string;
}) {
  const filter = active ? (size === "thumbnail" ? "blur(3px) saturate(0.15)" : "blur(6px) saturate(0.15)") : "none";

  if (size === "thumbnail") {
    return (
      <div
        className={cn("h-16 w-20 overflow-hidden rounded-md border border-rule", className)}
        aria-hidden="true"
      >
        <div
          className="scale-[0.29] origin-top-left transition-[filter] duration-500 motion-reduce:transition-none"
          style={{ filter }}
        >
          <PageMockup />
        </div>
      </div>
    );
  }

  return (
    <div className={cn("grid gap-4 sm:grid-cols-2", className)}>
      <div className="overflow-hidden rounded-md border border-rule">
        <div className="transition-[filter] duration-500 motion-reduce:transition-none" style={{ filter }}>
          <PageMockup />
        </div>
      </div>
      <div className="rounded-md border border-rule bg-paper-sunk p-3">
        <p className="label-mono mb-2">What it actually perceives</p>
        <ol className="space-y-1 font-mono text-xs text-ink-2">
          {READING_ORDER.map((line, i) => (
            <li key={i} className={cn("border-b border-rule/60 py-1 last:border-0", i === READING_ORDER.length - 1 && "text-critical")}>
              {i + 1}. {line}
            </li>
          ))}
        </ol>
      </div>
    </div>
  );
}
