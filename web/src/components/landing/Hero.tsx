import { useState, type ReactNode } from "react";
import { Link } from "react-router-dom";
import { AnimatePresence, motion } from "motion/react";
import { ArrowRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import { SeverityTag } from "@/components/SeverityTag";
import { PageMockup } from "@/components/personas/PageMockup";
import { AccessibilityRestrictedView } from "@/components/personas/AccessibilityRestrictedView";
import { useDemoRun } from "@/hooks/useDemoRun";
import { cn } from "@/lib/utils";
import { containerVariants, itemVariants, ruleVariants, transition } from "@/lib/motion";

/**
 * M6b: added a real toggle (Wispr's hero has a small interactive switch
 * demo; this is SimUX's honest equivalent) that swaps the specimen
 * panel between a plain page view and M5's actual
 * AccessibilityRestrictedView — genuine component state, not a
 * decorative animation. This replaces M6's static specimen card, which
 * only ever showed the "after" (the finding) — this version shows the
 * "before" too (the page looks fine) so the restriction's actual effect
 * is visible, not just described.
 */
export function Hero() {
  const run = useDemoRun();
  const specimen = run.findings.find((f) => f.showcase && f.personaId === "accessibility")!;
  const [view, setView] = useState<"normal" | "accessibility">("normal");

  return (
    <section className="relative overflow-hidden pb-20 pt-14 md:pb-28 md:pt-20">
      <div className="container">
        <div className="grid items-center gap-12 lg:grid-cols-12 lg:gap-16">
          <motion.div
            variants={containerVariants}
            initial="hidden"
            animate="visible"
            className="lg:col-span-7"
          >
            <motion.p variants={itemVariants} className="eyebrow-sans">
              Detect · Ground · Fix · Verify
            </motion.p>

            <motion.h1 variants={itemVariants} className="mt-5 max-w-[17ch] text-d1 font-hero">
              Some users can&rsquo;t see your screen.
              <br />
              <span className="relative inline-block italic">
                Test like it.
                {/* M6c: a physical-feeling mark under the emphasis line,
                    not just italic styling — draws in after the words
                    arrive, reusing the same self-draw mechanism as
                    SectionHeading's rule (ruleVariants), not a new one. */}
                <motion.span
                  variants={ruleVariants}
                  className="absolute -bottom-1 left-0 h-[3px] w-full origin-left rounded-full bg-ink/70"
                  aria-hidden="true"
                />
              </span>
            </motion.h1>

            <motion.p
              variants={itemVariants}
              className="mt-6 max-w-[54ch] text-lg leading-relaxed text-ink-2"
            >
              SimUX runs personas that are genuinely restricted — not told to roleplay — through
              real tasks on your product. One sees only what a screen reader would; another clicks
              the way an unsteady hand does. Every finding is grounded in a verbatim quote from
              WCAG 2.2 or Nielsen, and says what to change on your page.
            </motion.p>

            <motion.div variants={itemVariants} className="mt-9 flex flex-wrap items-center gap-3">
              <Button asChild size="lg" className="group">
                <Link to="/new-run">
                  See it in action
                  <ArrowRight className="h-4 w-4 transition-transform duration-200 group-hover:translate-x-1" />
                </Link>
              </Button>
              <Button asChild size="lg" variant="outline">
                <a href="#how">How it works</a>
              </Button>
            </motion.div>

            <motion.p variants={itemVariants} className="mt-6 font-mono text-xs text-ink-3">
              A prototype of the finished product — nothing here is running live yet.
            </motion.p>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 28 }}
            animate={{ opacity: 1, y: 0 }}
            transition={transition(0.8, 0.25)}
            className="lg:col-span-5"
          >
            <div className="card-chart overflow-hidden">
              <div className="flex items-center justify-between border-b border-rule px-4 py-3">
                <span className="label-mono">Same page, two ways of testing it</span>
              </div>

              {/* The toggle — real state, not decoration. */}
              <div className="flex gap-1 border-b border-rule bg-paper-sunk p-1.5">
                <ToggleButton active={view === "normal"} onClick={() => setView("normal")}>
                  Normal view
                </ToggleButton>
                <ToggleButton
                  active={view === "accessibility"}
                  onClick={() => setView("accessibility")}
                >
                  Accessibility view
                </ToggleButton>
              </div>

              <div className="p-4">
                <AnimatePresence mode="wait">
                  {view === "normal" ? (
                    <motion.div
                      key="normal"
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      exit={{ opacity: 0 }}
                      transition={transition(0.25)}
                    >
                      <div className="flex justify-center">
                        <PageMockup />
                      </div>
                      <p className="mt-3 text-center text-sm text-ink-2">
                        What a sighted tester sees. Looks fine.
                      </p>
                    </motion.div>
                  ) : (
                    <motion.div
                      key="accessibility"
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      exit={{ opacity: 0 }}
                      transition={transition(0.25)}
                    >
                      <AccessibilityRestrictedView size="full" />
                      <div className="mt-4 border-t border-rule pt-3">
                        <div className="flex items-center justify-between">
                          <span className="font-mono text-xs uppercase tracking-wide text-ink-3">
                            What that produces
                          </span>
                          <SeverityTag severity={specimen.severity} />
                        </div>
                        <h3 className="mt-2 font-display text-sm font-bold leading-snug text-ink">
                          {specimen.title}
                        </h3>
                        {specimen.citation && (
                          <p className="mt-2 font-mono text-xs text-ink-3">
                            Grounded in {specimen.citation.id}
                          </p>
                        )}
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>
            </div>
          </motion.div>
        </div>
      </div>
    </section>
  );
}

function ToggleButton({
  active,
  onClick,
  children,
}: {
  active: boolean;
  onClick: () => void;
  children: ReactNode;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      aria-pressed={active}
      className={cn(
        "flex-1 rounded-sm px-3 py-2 font-display text-sm font-medium transition-colors duration-200",
        active ? "bg-ink text-paper-raised" : "text-ink-2 hover:bg-ink/[0.05]",
      )}
    >
      {children}
    </button>
  );
}
