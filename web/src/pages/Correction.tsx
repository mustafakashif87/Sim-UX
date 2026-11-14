import { SiteNav } from "@/components/SiteNav";
import { Footer } from "@/components/Footer";

/**
 * M11 — deliberately the least-polished screen in the app
 * (POC_SPEC.md rule 4: an honest maturity gradient, not uniform
 * polish across all six modules). No `motion`, no `useDemoRun()`
 * fixture data, no interactivity, no animation — a plain static panel
 * is the correct amount of effort here, not something to "finish"
 * later. Compare directly against any other screen: this one should
 * read as obviously thinner on sight, not something that needs
 * explaining to a panel.
 *
 * Content is a compressed paraphrase of the proposal's own §2.2.5
 * (Correction / Learning Layer) description — not fixture data, since
 * this concept has no synthetic "case" to fake without contradicting
 * "planned for FYP-II."
 */
export default function Correction() {
  return (
    <>
      <SiteNav variant="app" />
      <main className="container py-20">
        <p className="label-mono">Correction / Learning</p>
        <h1 className="mt-3 font-display text-3xl font-bold tracking-tight text-ink">Not built yet.</h1>
        <p className="mt-4 max-w-[56ch] text-ink-2">
          Planned for FYP-II. This layer will store both fix-verification outcomes and operator
          corrections as cases, then use embedding-based similarity retrieval to surface related
          past cases before a new judgment is finalized — the one mechanism through which the
          system incorporates feedback from its own results and from human review.
        </p>

        <div className="mt-10 max-w-lg border border-rule p-6">
          <p className="label-mono">Planned for FYP-II</p>
          <pre className="mt-4 overflow-x-auto font-mono text-xs leading-relaxed text-ink-2">
            {`Fix-verify outcome ┐
                    ├─▶ Case store ─▶ New judgment
Operator correction ┘`}
          </pre>
        </div>
      </main>
      <Footer />
    </>
  );
}
