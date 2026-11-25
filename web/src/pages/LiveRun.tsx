import { Link, useParams } from "react-router-dom";
import { SiteNav } from "@/components/SiteNav";
import { Footer } from "@/components/Footer";
import { SeverityTag } from "@/components/SeverityTag";
import { useRun } from "@/hooks/useRun";
import {
  ENDED,
  PERSONAS,
  severityTag,
  type Action,
  type Finding,
  type PersonaId,
  type RunStatus,
  type StepRecord,
} from "@/lib/api";
import { cn } from "@/lib/utils";

/**
 * One real run, live: every step as the loop writes it, with the intended
 * and executed action side by side so each injected mistake is visible,
 * then the findings with their verified citations. Ungrounded findings are
 * labelled, never hidden (spec: Live interface, Running and Results).
 */

const STATUS_TEXT: Record<RunStatus, string> = {
  queued: "Waiting for a free browser",
  running: "Running",
  succeeded: "Task completed",
  gave_up: "The persona gave up",
  step_cap: "Ran out of steps",
  aborted_provider: "Stopped: the model could not answer",
  crashed: "Stopped: the harness crashed",
  failed: "Could not start",
};

export default function LiveRun() {
  const { runId = "" } = useParams();
  const { run, steps, error } = useRun(runId);
  const status = run?.status;
  const ended = status ? ENDED.has(status) : false;
  const persona = (run?.request?.persona ?? run?.meta?.persona) as PersonaId | undefined;
  const page =
    run?.request?.page ??
    run?.request?.url ??
    (run?.request?.task ? "your page" : run?.meta?.page?.replace(/\.html$/, ""));
  const condition = run?.request?.condition ?? run?.meta?.condition ?? "persona";
  const seed = run?.meta?.seed ?? run?.request?.seed;

  return (
    <>
      <SiteNav variant="app" />
      <main className="container py-20 md:py-28">
        <p className="eyebrow-sans">{ended ? "Run finished" : "Running"}</p>
        <h1 className="mt-3 font-hero text-d2 text-ink">
          {persona ? PERSONAS[persona]?.name ?? persona : "Run"} on {page ?? "…"}
        </h1>
        <p className="mt-4 font-mono text-[0.8125rem] text-ink-3">
          {condition === "baseline" ? "Baseline (limits off)" : "Persona limits on"} · seed{" "}
          {seed ?? "default"}
          {run?.meta?.model_id && <> · model {run.meta.model_id}</>} · run {runId}
        </p>

        {error && (
          <p role="alert" className="mt-8 rounded-lg border border-critical/45 p-4 text-ink">
            {error}
          </p>
        )}

        {status && (
          <p className="mt-8 flex items-center gap-3 text-ink" aria-live="polite">
            {!ended && <span className="h-2.5 w-2.5 animate-pulse rounded-full bg-ink" aria-hidden />}
            <span className="font-display text-xl font-bold">{STATUS_TEXT[status]}</span>
            <span className="text-ink-3">
              after {steps.length} {steps.length === 1 ? "step" : "steps"}
            </span>
          </p>
        )}
        {run?.error && <p className="mt-2 font-mono text-sm text-ink-2">{run.error}</p>}
        {run?.meta?.error && <p className="mt-2 font-mono text-sm text-ink-2">{run.meta.error}</p>}

        <StepTable steps={steps} />

        {ended && <Findings findings={run?.findings ?? []} />}

        <Link
          to="/new-run"
          className="mt-12 inline-block font-mono text-[0.6875rem] uppercase tracking-wide text-ink-3 underline decoration-rule underline-offset-4 hover:text-ink hover:decoration-ink"
        >
          Start another run →
        </Link>
      </main>
      <Footer />
    </>
  );
}

function describe(action: Action | null): string {
  if (!action) return "(nothing)";
  const target = action.ref ?? action.key ?? "";
  const text = action.text !== null ? ` "${action.text}"` : "";
  return `${action.action} ${target}${text}`.trim();
}

function StepTable({ steps }: { steps: StepRecord[] }) {
  if (steps.length === 0) return null;
  return (
    <div className="mt-10 overflow-x-auto rounded-xl border border-rule">
      <table className="w-full text-left text-sm">
        <caption className="sr-only">Steps: what the model intended and what reached the browser</caption>
        <thead className="font-mono text-[0.6875rem] uppercase tracking-wide text-ink-3">
          <tr className="border-b border-rule">
            <th scope="col" className="px-4 py-3">Step</th>
            <th scope="col" className="px-4 py-3">Intended</th>
            <th scope="col" className="px-4 py-3">Executed</th>
            <th scope="col" className="px-4 py-3">Mistake</th>
            <th scope="col" className="px-4 py-3">Result</th>
            <th scope="col" className="px-4 py-3">Goal</th>
          </tr>
        </thead>
        <tbody>
          {steps.map((s) => (
            <tr
              key={s.step}
              className={cn("border-b border-rule/60 align-top last:border-0", s.perturbation && "bg-caution/10")}
            >
              <td className="px-4 py-3 font-mono tabular-nums">{s.step}</td>
              <td className="px-4 py-3">
                <span className="font-mono">{describe(s.intended_action)}</span>
                {s.intended_action.thought && (
                  <span className="mt-1 block text-[0.8125rem] text-ink-3">{s.intended_action.thought}</span>
                )}
              </td>
              <td className="px-4 py-3 font-mono">{describe(s.executed_action)}</td>
              <td className="px-4 py-3 font-mono">{s.perturbation ?? "–"}</td>
              <td className="px-4 py-3 font-mono">{s.result}</td>
              <td className="px-4 py-3">{s.goal_reached ? "reached" : ""}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function Findings({ findings }: { findings: Finding[] }) {
  return (
    <section aria-labelledby="findings-heading" className="mt-12">
      <h2 id="findings-heading" className="font-display text-2xl font-bold text-ink">
        Findings
      </h2>
      {findings.length === 0 && <p className="mt-3 text-ink-2">No findings on this run.</p>}
      {findings.length > 0 && (
        <p className="mt-3 text-ink-2">
          {findings.length} {findings.length === 1 ? "change" : "changes"} to make, most severe
          first. Each is tied to the step where it happened and cites the guideline it breaks.
        </p>
      )}
      <ul className="mt-4 space-y-5">
        {findings.map((f) => (
          <li key={f.finding_id} className="card-chart p-6">
            <div className="flex flex-wrap items-center gap-3">
              <SeverityTag severity={severityTag(f.severity)} />
              <span className="font-mono text-sm text-ink">{f.signal}</span>
              <span className="text-sm text-ink-3">
                severity {f.severity} of 4 · confidence {f.confidence.toFixed(2)} · evidence step
                {f.evidence_steps.length === 1 ? "" : "s"} {f.evidence_steps.join(", ")}
              </span>
            </div>
            {f.problem && <p className="mt-3 font-display text-lg font-bold text-ink">{f.problem}</p>}
            {f.where?.path && (
              <p className="mt-2 text-sm text-ink-2">
                Where:{" "}
                <code className="font-mono text-ink">{f.where.element ?? "the whole page"}</code>
                {" on "}
                <code className="font-mono text-ink">{f.where.path}</code>
                {f.where.thought && (
                  <span className="text-ink-3"> · the persona was trying to: {f.where.thought}</span>
                )}
              </p>
            )}
            {f.fix && (
              <div className="mt-3 rounded-lg border border-ink/20 bg-paper-raised p-4">
                <p className="font-mono text-[0.6875rem] uppercase tracking-wide text-ink-3">
                  Change on the page
                </p>
                <p className="mt-1 text-ink">{f.fix}</p>
              </div>
            )}
            <p className="mt-2 font-mono text-[0.8125rem] text-ink-3">
              Candidates: {f.candidate_criteria.join(" / ")}
            </p>
            {f.citations.length === 0 ? (
              <p className="mt-3 text-sm text-ink-2">
                Ungrounded: no quote passed verification, so confidence is halved.
              </p>
            ) : (
              <ul className="mt-3 space-y-3">
                {f.citations.map((c) => (
                  <li key={c.criterion_id}>
                    <blockquote className="border-l-2 border-ink pl-4 font-body text-ink-2">
                      “{c.quote}”
                    </blockquote>
                    <p className="mt-1 pl-4 font-mono text-[0.75rem] text-ink-3">
                      {c.criterion_id} · verified verbatim against the corpus
                    </p>
                  </li>
                ))}
              </ul>
            )}
          </li>
        ))}
      </ul>
    </section>
  );
}
