import { Link } from "react-router-dom";
import { SiteNav } from "@/components/SiteNav";
import { Footer } from "@/components/Footer";
import { Button } from "@/components/ui/button";
import { useDemoRun } from "@/hooks/useDemoRun";

// M4 placeholder — the real six-stage animated walkthrough (with the
// blur/jitter persona metaphors playing live) lands in M8.
export default function Running() {
  const run = useDemoRun();

  return (
    <>
      <SiteNav variant="app" />
      <main className="container py-20">
        <p className="label-mono">M4 placeholder</p>
        <h1 className="mt-3 text-d1 font-hero">Running</h1>
        <p className="mt-4 max-w-[58ch] text-ink-2">
          Full animated stage walkthrough lands in M8. Stages: {run.stages.map((s) => s.label).join(" → ")}.
        </p>
        <Button asChild className="mt-8">
          <Link to="/results">Continue to results →</Link>
        </Button>
      </main>
      <Footer />
    </>
  );
}
