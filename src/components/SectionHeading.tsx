import { cn } from "@/lib/utils";

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
 *
 * Scroll-triggered reveal (word-by-word title rise, self-drawing rule,
 * fade+rise on the eyebrow/lede) removed by request — everything renders
 * in its final state immediately, no whileInView.
 */
export function SectionHeading({
  eyebrow,
  title,
  lede,
  inverse = false,
  className,
}: SectionHeadingProps) {
  return (
    <div className={cn("max-w-3xl", className)}>
      <p className={cn("eyebrow-sans", inverse && "text-paper/65")}>{eyebrow}</p>

      <div className={cn("my-4 h-px", inverse ? "bg-paper/25" : "bg-rule")} />

      <h2 className={cn("text-d2 font-hero", inverse && "text-paper")}>{title}</h2>

      {lede && (
        <p
          className={cn(
            "mt-5 max-w-[62ch] text-lg leading-relaxed",
            inverse ? "text-paper/70" : "text-ink-2",
          )}
        >
          {lede}
        </p>
      )}
    </div>
  );
}
