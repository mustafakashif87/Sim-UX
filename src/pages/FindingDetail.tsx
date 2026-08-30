import { Link, useParams } from "react-router-dom";
import { SiteNav } from "@/components/SiteNav";
import { Footer } from "@/components/Footer";
import { useDemoRun } from "@/hooks/useDemoRun";

// M4 placeholder — the full fix -> sandbox -> verify showcase
// walkthrough (for the two confirmed showcase findings only) lands in
// M10. This confirms the dynamic route param resolves against real
// fixture data.
export default function FindingDetail() {
  const { findingId } = useParams<{ findingId: string }>();
  const run = useDemoRun();
  const finding = run.findings.find((f) => f.id === findingId);

  return (
    <>
      <SiteNav variant="app" />
      <main className="container py-20">
        <p className="label-mono">M4 placeholder</p>
        <h1 className="mt-3 text-d1 font-hero">Finding detail</h1>
        {finding ? (
          <div className="mt-4 max-w-[60ch]">
            <p className="text-ink-2">{finding.title}</p>
            <p className="mt-2 text-sm text-ink-3">
              {finding.showcase
                ? "This finding has the full fix → sandbox → verify walkthrough (M10)."
                : "This is a plain finding — no walkthrough (correct, per POC_SPEC.md)."}
            </p>
          </div>
        ) : (
          <p className="mt-4 text-ink-2">No finding matches id “{findingId}”.</p>
        )}
        <Link to="/results" className="mt-8 inline-block underline">
          ← Back to results
        </Link>
      </main>
      <Footer />
    </>
  );
}
