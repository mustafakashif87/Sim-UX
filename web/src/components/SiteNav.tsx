import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { motion } from "motion/react";
import { ArrowLeft, ArrowRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import { BrandMark } from "@/components/BrandMark";
import { EASE } from "@/lib/motion";

// Rebranded from site-doctor: anchors point at SimUX's own landing
// sections (built in M6), the CTA goes to /new-run (persona selection)
// instead of /app, and copy no longer references audits. Structure and
// motion (the full-bar-to-pill scroll transition) are unchanged.
const SECTIONS = [
  { href: "#personas", label: "Personas" },
  { href: "#how", label: "How it works" },
  { href: "/results", label: "Results" },
];

const SHAPE = {
  full: {
    maxWidth: 1200,
    borderRadius: 0,
    y: 0,
    height: 68,
    paddingLeft: 0,
    paddingRight: 0,
    backgroundColor: "hsl(var(--ink) / 0)",
    borderColor: "hsl(var(--paper) / 0)",
    boxShadow: "0 0 0 0 hsl(var(--ink) / 0)",
  },
  pill: {
    maxWidth: 940,
    borderRadius: 999,
    y: 12,
    height: 56,
    // Was 20/12 — the asymmetry read as "See it in action" sitting too
    // close to the pill's right edge relative to the logo's left
    // clearance. Matched to the logo's own 20px so both ends breathe
    // the same amount.
    paddingLeft: 20,
    paddingRight: 20,
    backgroundColor: "hsl(var(--ink) / 1)",
    borderColor: "hsl(var(--paper) / 0.16)",
    boxShadow: "0 20px 44px -24px hsl(var(--ink) / 0.85)",
  },
} as const;

interface SiteNavProps {
  /** "landing" gets section anchors; "app" gets a way back. */
  variant?: "landing" | "app";
}

export function SiteNav({ variant = "landing" }: SiteNavProps) {
  const [lifted, setLifted] = useState(false);

  useEffect(() => {
    // Hysteresis: without a gap between the two thresholds the header
    // flickers between shapes when you rest the scroll right on the line.
    const onScroll = () =>
      setLifted((current) => (current ? window.scrollY > 40 : window.scrollY > 72));
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  return (
    <motion.header
      initial={{ y: -24, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ duration: 0.6, ease: EASE }}
      className="sticky top-0 z-50"
    >
      {/* The full-bleed bar. Lives behind the content and hands over to the
          pill on scroll, so one of the two is always solid. */}
      <motion.div
        className="absolute inset-0 border-b border-paper/10 bg-ink"
        initial={false}
        animate={{ opacity: lifted ? 0 : 1 }}
        transition={{ duration: 0.4, ease: EASE }}
        aria-hidden="true"
      />

      <div className="container relative h-[68px]">
        <motion.div
          animate={lifted ? SHAPE.pill : SHAPE.full}
          initial={false}
          transition={{ duration: 0.5, ease: EASE }}
          className="mx-auto flex items-center justify-between gap-6 border"
        >
          <Link to="/" aria-label="SimUX — home" className="shrink-0">
            <BrandMark inverse />
          </Link>

          {variant === "landing" ? (
            <>
              <nav className="hidden items-center gap-8 md:flex" aria-label="Sections">
                {SECTIONS.map((section) => (
                  <a
                    key={section.href}
                    href={section.href}
                    className="group relative font-display text-[0.8125rem] font-medium text-paper/70 transition-colors hover:text-paper"
                  >
                    {section.label}
                    <span className="absolute -bottom-1 left-0 h-px w-0 bg-paper transition-all duration-300 group-hover:w-full" />
                  </a>
                ))}
              </nav>
              <Button asChild size="sm" variant="inverse" className="group shrink-0">
                <Link to="/new-run">
                  See it in action
                  <ArrowRight className="h-3.5 w-3.5 transition-transform duration-200 group-hover:translate-x-0.5" />
                </Link>
              </Button>
            </>
          ) : (
            <Button asChild variant="ghostInverse" size="sm" className="group shrink-0">
              <Link to="/">
                <ArrowLeft className="h-3.5 w-3.5 transition-transform duration-200 group-hover:-translate-x-0.5" />
                Back to home
              </Link>
            </Button>
          )}
        </motion.div>
      </div>
    </motion.header>
  );
}
