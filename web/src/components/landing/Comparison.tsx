import { Link } from "react-router-dom";
import { SectionHeading } from "@/components/SectionHeading";
import { ROWS, SIMUX_TOTAL, detectedBy } from "@/lib/evaluation";

/**
 * Single-prompt critique against SimUX, on the measured evaluation
 * (src/data/evaluation.json): the same 41 seeded bugs, each with a clean
 * twin. The points below describe what is built, nothing planned.
 */

const CRITIQUE_POINTS = [
  "The persona is a sentence in the prompt, not a limit",
  "Reads the page once; never acts, so never sees behaviour",
  "Citations are recalled by the model and can be wrong",
  "Says what looks wrong, not where it broke a real task",
];

const SIMUX_POINTS = [
  "Persona limits are enforced in code: what it sees, can do and remembers",
  "Attempts the real task in a real browser; the harness decides success",
  "Every quote is checked verbatim against WCAG 2.2 and Nielsen",
  "Each finding names the step, the element and the change to make",
];

export function Comparison() {
  const total = ROWS.length;
  return (
    <section className="border-t border-rule py-20 md:py-28">
      <div className="container">
        <SectionHeading
          eyebrow="Why not just ask a chat model"
          title="The gap this closes, measured."
          lede={`On ${total} seeded bugs, each with a clean twin page, a single-prompt LLM review found ${detectedBy("single_prompt")} and axe-core found ${detectedBy("axe")}. SimUX found ${SIMUX_TOTAL}.`}
        />

        <div className="mt-14 grid gap-6 md:grid-cols-2">
          <ComparisonColumn
            title={`Single-prompt critique: ${detectedBy("single_prompt")}/${total}`}
            points={CRITIQUE_POINTS}
            good={false}
          />
          <ComparisonColumn title={`SimUX: ${SIMUX_TOTAL}/${total}`} points={SIMUX_POINTS} good />
        </div>
        <Link
          to="/results"
          className="mt-8 inline-block font-mono text-[0.75rem] uppercase tracking-wide text-ink-3 underline decoration-rule underline-offset-4 hover:text-ink"
        >
          See every bug and every system →
        </Link>
      </div>
    </section>
  );
}

function ComparisonColumn({
  title,
  points,
  good,
}: {
  title: string;
  points: string[];
  good: boolean;
}) {
  return (
    <div className={good ? "card-chart-lg bg-persona-accessibility p-6" : "card-chart-lg bg-paper-sunk p-6"}>
      <h3 className="font-display text-lg font-bold tracking-tight text-ink">{title}</h3>
      <ul className="mt-4 space-y-3">
        {points.map((point) => (
          <li key={point} className="flex items-start gap-2.5">
            {good ? <Check /> : <X />}
            <span className="text-sm leading-relaxed text-ink-2">{point}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}

function Check() {
  return (
    <svg
      viewBox="0 0 24 24"
      className="mt-0.5 h-4 w-4 shrink-0"
      fill="none"
      stroke="hsl(var(--minor-ink))"
      strokeWidth={2.5}
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="M20 6 9 17l-5-5" />
    </svg>
  );
}

function X() {
  return (
    <svg
      viewBox="0 0 24 24"
      className="mt-0.5 h-4 w-4 shrink-0"
      fill="none"
      stroke="hsl(var(--ink-3))"
      strokeWidth={2.5}
      strokeLinecap="round"
    >
      <line x1="18" y1="6" x2="6" y2="18" />
      <line x1="6" y1="6" x2="18" y2="18" />
    </svg>
  );
}
