import { Link } from "react-router-dom";
import { motion } from "motion/react";
import { ArrowUpRight } from "lucide-react";
import { BrandMark } from "@/components/BrandMark";
import { containerVariantsSlow, inView, transition } from "@/lib/motion";

// Rebranded from site-doctor: copy describes SimUX's actual concept
// (restricted personas, grounded findings, a verified fix loop) instead
// of a crawl-audit-triage-fix bundle. The second strapline is a
// deliberate, permanent self-disclosure that this is a prototype —
// appears on every page since Footer is global chrome.
//
// Also dropped here: the screen-grid texture and the decorative Trace
// (ECG/vitals) motif that used to sit at the top of this band — both
// were Site Doctor's "clinical instrument" visual signature, with no
// Wispr equivalent. Plain dark band now, no texture, no monitor line.
//
// M6b: expanded from one link list to two columns, and added a large
// closing wordmark echoing Wispr's giant "Flow" mark at the bottom of
// their footer — built from the same three-dot motif as BrandMark, at
// large scale.
//
// Scroll-in fade+rise on the header block removed by request — that
// part just renders in its final state now, no whileInView. The
// closing dots/wordmark keep their own animation (spring-pop dots,
// clip-path wordmark wipe) — restored by request, since that's a
// pop/wipe beat, not a generic fade-in.
const EXPLORE_LINKS = [
  { to: "/#personas", label: "Personas" },
  { to: "/#how", label: "How it works" },
  { to: "/new-run", label: "See it in action" },
];

const ABOUT_LINKS = [
  { to: "/#standards", label: "Grounded in standards" },
  { to: "/correction", label: "What's not built yet" },
];

export function Footer() {
  return (
    <footer className="relative overflow-hidden bg-ink text-paper">
      <div className="container relative py-14 md:py-16">
        <div className="flex flex-col justify-between gap-10 sm:flex-row sm:items-start">
          <div className="max-w-[42ch]">
            <BrandMark inverse />
            <p className="mt-4 text-[0.9375rem] leading-relaxed text-paper/60">
              A walkthrough of SimUX: personas that are genuinely restricted, not roleplayed,
              attempting real tasks, grounding what they find in real sources, and proposing a fix
              that gets sandboxed and verified before anyone trusts it.
            </p>
          </div>

          <div className="flex gap-16">
            <FooterColumn heading="Explore" links={EXPLORE_LINKS} />
            <FooterColumn heading="About" links={ABOUT_LINKS} />
          </div>
        </div>

        <div className="mt-12 flex flex-wrap items-center justify-between gap-3 border-t border-paper/15 pt-6">
          <p className="font-mono text-micro uppercase text-paper/55">
            Detect · Ground · Fix · Verify
          </p>
          <p className="font-mono text-micro uppercase text-paper/55">
            Proof-of-concept prototype · Nothing here is running live
          </p>
        </div>

        <motion.div
          variants={containerVariantsSlow}
          initial="hidden"
          whileInView="visible"
          viewport={inView}
          className="mt-10 flex items-center gap-4 border-t border-paper/15 pt-10"
        >
          {/* Real bounce (spring, not the eased fade+rise itemVariants
              uses everywhere else) — each dot drops and springs back to
              its resting position, overshooting slightly on the way. */}
          <div className="flex gap-2" aria-hidden="true">
            {[0, 1, 2].map((i) => (
              <motion.span
                key={i}
                variants={{
                  hidden: { opacity: 0, y: -18 },
                  visible: {
                    opacity: 1,
                    y: 0,
                    transition: { type: "spring", stiffness: 500, damping: 11 },
                  },
                }}
                className="h-3.5 w-3.5 rounded-full bg-paper"
              />
            ))}
          </div>
          {/* Clip-path reveal instead of a generic fade+rise — the
              letters "resolve" into view after the dots finish, a small
              symbolic beat (the personas/dots resolve into the product
              name). */}
          <motion.span
            variants={{
              hidden: { clipPath: "inset(0 100% 0 0)" },
              visible: { clipPath: "inset(0 0% 0 0)", transition: transition(0.7) },
            }}
            className="font-display text-5xl font-bold tracking-tight text-paper md:text-7xl"
          >
            SimUX
          </motion.span>
        </motion.div>
      </div>
    </footer>
  );
}

function FooterColumn({
  heading,
  links,
}: {
  heading: string;
  links: { to: string; label: string }[];
}) {
  return (
    <div>
      <p className="font-mono text-[0.6875rem] uppercase tracking-wide text-paper/40">{heading}</p>
      <nav className="mt-3 flex flex-col gap-1" aria-label={heading}>
        {links.map((link) => (
          <Link
            key={link.to}
            to={link.to}
            className="group inline-flex items-center gap-1.5 py-1 font-display text-sm font-medium text-paper/65 transition-colors hover:text-paper"
          >
            {link.label}
            <ArrowUpRight
              className="h-3.5 w-3.5 opacity-0 transition-all duration-200 group-hover:translate-x-0.5 group-hover:opacity-100"
              aria-hidden="true"
            />
          </Link>
        ))}
      </nav>
    </div>
  );
}
