import * as React from "react";
import * as ToggleGroupPrimitive from "@radix-ui/react-toggle-group";
import { cn } from "@/lib/utils";

// Used by NewRun.tsx (M7) for the persona-selection cards. `type="multiple"`
// there — a run tests "whichever personas you picked" (plural, see the
// PipelineStages/Aggregate copy and fixture data), so this is a genuine
// multi-select toggle set, not a single-select radio group, despite the
// milestone plan's own text saying "radio-group." See CLAUDE.md §10 for
// the full reasoning.
//
// Root renders `role="group"` with roving-tabindex arrow-key navigation
// between items; each Item is a real `<button>` with `aria-pressed`/
// `data-state="on"|"off"` managed by Radix — the persona card's own
// selected-state styling reacts to that via `group-data-[state=on]:`
// Tailwind variants (needs `className="group"` on the Item, or on
// whatever wraps it) rather than tracking a duplicate "am I selected"
// prop just for styling.

const ToggleGroup = React.forwardRef<
  React.ElementRef<typeof ToggleGroupPrimitive.Root>,
  React.ComponentPropsWithoutRef<typeof ToggleGroupPrimitive.Root>
>(({ className, ...props }, ref) => (
  <ToggleGroupPrimitive.Root ref={ref} className={cn(className)} {...props} />
));
ToggleGroup.displayName = ToggleGroupPrimitive.Root.displayName;

const ToggleGroupItem = React.forwardRef<
  React.ElementRef<typeof ToggleGroupPrimitive.Item>,
  React.ComponentPropsWithoutRef<typeof ToggleGroupPrimitive.Item>
>(({ className, ...props }, ref) => (
  <ToggleGroupPrimitive.Item
    ref={ref}
    className={cn(
      // Full button-element reset — Radix doesn't style this itself, and
      // without it a default browser <button> box shows through behind
      // whatever card content is passed as children.
      "group block w-full appearance-none rounded-2xl border-0 bg-transparent p-0 text-left font-inherit text-inherit",
      "transition-transform duration-200 ease-out active:scale-[0.98]",
      "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ink focus-visible:ring-offset-2 focus-visible:ring-offset-paper",
      "disabled:cursor-not-allowed disabled:opacity-50",
      className,
    )}
    {...props}
  />
));
ToggleGroupItem.displayName = ToggleGroupPrimitive.Item.displayName;

export { ToggleGroup, ToggleGroupItem };
