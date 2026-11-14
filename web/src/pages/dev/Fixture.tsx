// M3 verification page — dev-only, unlinked from any nav. Dumps
// useDemoRun()'s full output so every field a downstream screen will
// need can be checked before M4+ builds screens against it, and so
// each citation's text can be read here directly for a side-by-side
// check against its real source (see fixtures/citations.ts's sourcing
// comments). Must be removed/excluded from the production build and
// nav by M12, same as the M1/M2 Tokens page.

import { useDemoRun } from "@/hooks/useDemoRun";

export default function Fixture() {
  const run = useDemoRun();

  return (
    <div className="container space-y-8 py-12">
      <header>
        <p className="label-mono">M3 verification — dev only</p>
        <h1 className="mt-3 text-d2 font-display">useDemoRun() output</h1>
      </header>

      <section>
        <h2 className="text-d3">Citations — read these against the real source</h2>
        <ul className="mt-4 space-y-4">
          {run.findings
            .filter((f) => f.citation)
            .map((f) => (
              <li key={f.id} className="card-chart p-4">
                <p className="label-mono">
                  {f.citation!.id} — {f.citation!.title}
                </p>
                <p className="mt-2 text-sm text-ink-2">&ldquo;{f.citation!.text}&rdquo;</p>
                <a
                  href={f.citation!.url}
                  target="_blank"
                  rel="noreferrer"
                  className="mt-2 inline-block font-mono text-xs text-ink-3 underline"
                >
                  {f.citation!.url}
                </a>
              </li>
            ))}
        </ul>
      </section>

      <section>
        <h2 className="text-d3">Full raw output</h2>
        <pre className="card-chart mt-4 overflow-x-auto p-4 text-xs">
          {JSON.stringify(run, null, 2)}
        </pre>
      </section>
    </div>
  );
}
