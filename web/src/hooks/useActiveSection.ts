import { useEffect, useRef } from "react";
import { useInView } from "motion/react";

/**
 * Tracks which of N stacked blocks is currently in the "focus band" of
 * the viewport, via IntersectionObserver margin, for scroll-driven
 * sticky-panel sections (CapabilityGrid). Each block calls this with
 * its own index and a shared `setActive` callback; whichever block is
 * in the band last wins. Since `onActive` only ever fires forward
 * (there's no "nothing is active" reset), a band a fast scroll can skip
 * clean over leaves the state stuck on whichever block fired last —
 * most visible on the final block, since nothing after it can correct
 * a miss. The band is intentionally wide (a 20%-tall slice, not a thin
 * line) to make that miss unlikely.
 *
 * The band is centered on the viewport (a 20%-tall slice straddling
 * the midpoint) — this has to match where the ONE shared sticky panel
 * actually locks (CapabilityGrid's inner sticky div uses `sticky top-1/2
 * -translate-y-1/2`, true vertical center, crossfading its content via
 * this hook's `active` index rather than rendering a separate panel per
 * block). A per-block sticky container (one independent panel per item)
 * and a near-top offset (`top-28`, 15%-35% band) were both tried and
 * reverted — see CapabilityGrid's own doc comment for why. If these two
 * values drift apart again, the symptom is the panel and the
 * highlighted text no longer corresponding — keep them in sync if
 * either value changes.
 *
 * Fixed-count usage only (call once per block, not in a loop) — this
 * satisfies React's rules of hooks and matches every current caller
 * (always a small, known number of blocks).
 */
const FOCUS_BAND = "-40% 0px -40% 0px";

export function useSectionInView(index: number, onActive: (i: number) => void) {
  const ref = useRef<HTMLDivElement>(null);
  const inView = useInView(ref, { margin: FOCUS_BAND });
  useEffect(() => {
    if (inView) onActive(index);
  }, [inView, index, onActive]);
  return ref;
}
