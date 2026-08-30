import { Link } from "react-router-dom";
import { SiteNav } from "@/components/SiteNav";
import { Footer } from "@/components/Footer";
import { useDemoRun } from "@/hooks/useDemoRun";

// M4 placeholder — the full severity/persona-grouped dashboard, hero UI
// Score, and run history land in M9. Links to each finding confirm the
// /results/:findingId route works with real ids from fixture data.
export default function Results() {
  const run = useDemoRun();

  return (
    <>
      <SiteNav variant="app" />
      <main className="container py-20">
        <p className="label-mono">M4 placeholder</p>
        <h1 className="mt-3 text-d1 font-hero">Results</h1>
        <p className="mt-4 max-w-[58ch] text-ink-2">
          Full dashboard (severity + persona grouping, UI Score, history) lands in M9.
        </p>
        <ul className="mt-8 space-y-2">
          {run.findings.map((f) => (
            <li key={f.id}>
              <Link to={`/results/${f.id}`} className="underline">
                {f.title}
              </Link>
            </li>
          ))}
        </ul>
      </main>
      <Footer />
    </>
  );
}
