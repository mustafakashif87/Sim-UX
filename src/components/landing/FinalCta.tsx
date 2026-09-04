import { Link } from "react-router-dom";
import { ArrowRight } from "lucide-react";
import { Button } from "@/components/ui/button";

/**
 * M6b: the flat `bg-stock-3` fill from M6 is replaced with a soft
 * persona-tint gradient (no real photography exists to use the way
 * Wispr's closing section does).
 *
 * Scroll-triggered reveal (scale-up card arrival, staggered heading/
 * copy/button fade-in) removed by request — the card now renders in
 * its final state immediately.
 */
export function FinalCta() {
  return (
    <section className="border-t border-rule py-20 md:py-28">
      <div className="container">
        <div className="card-chart-lg bg-gradient-to-br from-persona-accessibility to-persona-motor px-6 py-14 text-center md:px-10 md:py-20">
          <h2 className="text-d2 font-hero">See it in action.</h2>
          <p className="mx-auto mt-4 max-w-[50ch] text-[0.9375rem] leading-relaxed text-ink-2">
            Walk through the full flow — pick a persona, watch the pipeline run, and see what a
            grounded, verified finding actually looks like.
          </p>
          <div className="mt-8">
            <Button asChild size="lg" className="group">
              <Link to="/new-run">
                See it in action
                <ArrowRight className="h-4 w-4 transition-transform duration-200 group-hover:translate-x-1" />
              </Link>
            </Button>
          </div>
        </div>
      </div>
    </section>
  );
}
