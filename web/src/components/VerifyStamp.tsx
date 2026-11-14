import { cn } from "@/lib/utils";

/**
 * The pass/fail mark for a showcase finding's fix->sandbox->verify
 * walkthrough (M10). Uses M1's hard, zero-blur "stamp" shadows
 * deliberately — the opposite treatment from every other card's soft
 * `shadow-chart`/`shadow-lift` elevation, so this one reads as a
 * physical stamp pressed onto the page, not another floating panel.
 */
export function VerifyStamp({ result }: { result: "pass" | "fail" }) {
  const isPass = result === "pass";

  return (
    <div
      className={cn(
        "inline-flex -rotate-2 items-center gap-2 rounded-md border-2 bg-paper-raised px-4 py-2 font-display text-sm font-bold uppercase tracking-wide",
        isPass
          ? "border-minor text-[hsl(var(--minor-ink))] shadow-stamp-pass"
          : "border-critical text-[hsl(var(--critical-ink))] shadow-stamp-fail",
      )}
    >
      {isPass ? "Verified — fix holds" : "Verify failed"}
    </div>
  );
}
