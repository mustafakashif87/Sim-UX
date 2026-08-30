import { Link } from "react-router-dom";
import { motion } from "motion/react";
import { ArrowRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import { containerVariants, itemVariants, inView, transition } from "@/lib/motion";

/**
 * M6b: the flat `bg-stock-3` fill and plain fade-in from M6 are
 * replaced with a soft persona-tint gradient (no real photography
 * exists to use the way Wispr's closing section does) and a scale-up
 * arrival (0.98 -> 1, echoing the button press-down language elsewhere)
 * instead of a plain fade — a touch more presence for the page's last
 * moment before conversion.
 */
export function FinalCta() {
  return (
    <section className="border-t border-rule py-20 md:py-28">
      <div className="container">
        <motion.div
          initial={{ opacity: 0, scale: 0.98 }}
          whileInView={{ opacity: 1, scale: 1 }}
          viewport={inView}
          transition={transition(0.6)}
          className="card-chart-lg bg-gradient-to-br from-persona-accessibility to-persona-motor px-6 py-14 text-center md:px-10 md:py-20"
        >
          <motion.div
            variants={containerVariants}
            initial="hidden"
            whileInView="visible"
            viewport={inView}
          >
            <motion.h2 variants={itemVariants} className="text-d2 font-hero">
              See it in action.
            </motion.h2>
            <motion.p
              variants={itemVariants}
              className="mx-auto mt-4 max-w-[50ch] text-[0.9375rem] leading-relaxed text-ink-2"
            >
              Walk through the full flow — pick a persona, watch the pipeline run, and see what a
              grounded, verified finding actually looks like.
            </motion.p>
            <motion.div variants={itemVariants} className="mt-8">
              <Button asChild size="lg" className="group">
                <Link to="/new-run">
                  See it in action
                  <ArrowRight className="h-4 w-4 transition-transform duration-200 group-hover:translate-x-1" />
                </Link>
              </Button>
            </motion.div>
          </motion.div>
        </motion.div>
      </div>
    </section>
  );
}
