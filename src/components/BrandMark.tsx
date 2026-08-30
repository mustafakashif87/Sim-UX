import { cn } from "@/lib/utils";

interface BrandMarkProps {
  className?: string;
  /** Inverted for use on the dark footer band. */
  inverse?: boolean;
}

// The icon was originally a vitals-trace (ECG) glyph inherited from
// site-doctor — the clearest single piece of its "clinical instrument"
// visual metaphor. Replaced with three dots (one per persona), matching
// index.html's favicon, so the mark itself says "three personas," not
// "heart monitor."
export function BrandMark({ className, inverse = false }: BrandMarkProps) {
  return (
    <span className={cn("group inline-flex items-center gap-2.5", className)}>
      <span
        className={cn(
          "grid h-8 w-8 place-items-center rounded-md transition-transform duration-300 group-hover:-rotate-3",
          inverse ? "bg-paper text-ink" : "bg-ink text-paper",
        )}
        aria-hidden="true"
      >
        <svg viewBox="0 0 32 32" className="h-[16px] w-[16px]">
          <circle cx="7" cy="16" r="3" fill="currentColor" />
          <circle cx="16" cy="16" r="3" fill="currentColor" />
          <circle cx="25" cy="16" r="3" fill="currentColor" />
        </svg>
      </span>
      <span
        className={cn(
          "font-display text-[0.9375rem] font-bold tracking-tight",
          inverse ? "text-paper" : "text-ink",
        )}
      >
        SimUX
      </span>
    </span>
  );
}
