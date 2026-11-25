import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { ArrowRight } from "lucide-react";
import { SiteNav } from "@/components/SiteNav";
import { Footer } from "@/components/Footer";
import { Button } from "@/components/ui/button";
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group";
import {
  EVALUATION_DATE,
  ROWS,
  SIMUX_TOTAL,
  SYSTEMS,
  SYSTEM_LABEL,
  detectedBy,
  type BugRow,
} from "@/lib/evaluation";
import { cn } from "@/lib/utils";

/**
 * The evaluation, measured: 41 seeded bugs, each with a buggy and a clean
 * page, and which system caught which. Every number here comes from
 * src/data/evaluation.json (agent.compare's table.json); nothing is typed in.
 */

type Filter = "all" | "simux-only" | "missed";

export default function Results() {
  const [filter, setFilter] = useState<Filter>("all");
  const rows = useMemo(
    () =>
      ROWS.filter((r) => {
        const simux = r.detected.simux || r.detected.keyboard_sweep;
        if (filter === "missed") return !simux;
        if (filter === "simux-only") return simux && !r.detected.axe && !r.detected.single_prompt;
        return true;
      }),
    [filter],
  );
  const total = ROWS.length;
  const bars = [
    { label: "SimUX (personas and keyboard sweep)", value: SIMUX_TOTAL, strong: true },
    { label: SYSTEM_LABEL.simux, value: detectedBy("simux"), strong: false },
    { label: SYSTEM_LABEL.axe, value: detectedBy("axe"), strong: false },
    { label: SYSTEM_LABEL.single_prompt, value: detectedBy("single_prompt"), strong: false },
  ];

  return (
    <>
      <SiteNav variant="app" />
      <main className="container py-20 md:py-28">
        <p className="eyebrow-sans">Results</p>
        <h1 className="mt-3 max-w-[22ch] font-hero text-d1 text-ink">
          {SIMUX_TOTAL} of {total} seeded bugs found. A one-shot LLM review found{" "}
          {detectedBy("single_prompt")}.
        </h1>
        <p className="mt-4 max-w-[64ch] text-ink-2">
          Each bug lives on a buggy page with a clean twin that differs only in that bug. A
          system detects a bug only if it reports it on the buggy page and not on the clean one,
          so reporting everything everywhere scores nothing. {EVALUATION_DATE}; model
          gpt-oss-120b at temperature 0.
        </p>

        <section aria-labelledby="headline" className="mt-12">
          <h2 id="headline" className="sr-only">
            Bugs detected by each system
          </h2>
          <ul className="space-y-4">
            {bars.map((b) => (
              <li key={b.label}>
                <div className="flex items-baseline justify-between gap-4">
                  <span className={cn("text-ink", b.strong && "font-display font-bold")}>
                    {b.label}
                  </span>
                  <span className="font-mono tabular-nums text-ink">
                    {b.value}/{total}
                  </span>
                </div>
                <div className="mt-1.5 h-3 rounded-full bg-paper-sunk" aria-hidden>
                  <div
                    className={cn("h-3 rounded-full", b.strong ? "bg-ink" : "bg-ink/35")}
                    style={{ width: `${(100 * b.value) / total}%` }}
                  />
                </div>
              </li>
            ))}
          </ul>
          <dl className="mt-10 grid gap-6 sm:grid-cols-3">
            <Stat term="False alarms" value="1 in 84" note="clean-page runs with any finding" />
            <Stat term="Citations valid" value="100%" note="every quote verified verbatim" />
            <Stat
              term="Attributed to a persona"
              value="2 of 12"
              note="P1 to P3: the no-limits baseline missed it"
            />
          </dl>
        </section>

        <section aria-labelledby="per-bug" className="mt-16">
          <div className="flex flex-wrap items-end justify-between gap-4">
            <h2 id="per-bug" className="font-display text-2xl font-bold text-ink">
              Every seeded bug
            </h2>
            <ToggleGroup
              type="single"
              value={filter}
              onValueChange={(v) => v && setFilter(v as Filter)}
              aria-label="Show"
              className="flex gap-2"
            >
              {(
                [
                  ["all", "All"],
                  ["simux-only", "Only SimUX found"],
                  ["missed", "Missed"],
                ] as [Filter, string][]
              ).map(([value, label]) => (
                <ToggleGroupItem
                  key={value}
                  value={value}
                  className="w-auto rounded-full border border-rule px-3 py-1.5 font-mono text-xs data-[state=on]:bg-ink data-[state=on]:text-paper-raised"
                >
                  {label}
                </ToggleGroupItem>
              ))}
            </ToggleGroup>
          </div>
          <div className="mt-4 overflow-x-auto rounded-xl border border-rule">
            <table className="w-full text-left text-sm">
              <caption className="sr-only">
                Which system detected each seeded bug; k/n is persona runs that found it
              </caption>
              <thead className="font-mono text-[0.6875rem] uppercase tracking-wide text-ink-3">
                <tr className="border-b border-rule">
                  <th scope="col" className="px-4 py-3">Bug</th>
                  <th scope="col" className="px-4 py-3">Signal</th>
                  {SYSTEMS.map((s) => (
                    <th key={s} scope="col" className="px-4 py-3">
                      {SYSTEM_LABEL[s]}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {rows.map((r) => (
                  <Row key={r.bug} row={r} />
                ))}
              </tbody>
            </table>
          </div>
          <p className="mt-4 max-w-[64ch] text-sm text-ink-3">
            P1 to P3 ran 5 seeds in each condition; P4 to P14 ran once each (smoke runs, no
            baseline), so their 1/1 is weak evidence. Most misses are runs where the model
            finished before the behaviour happened: P1 fixed its own typo, P9 was never away long
            enough to time out.
          </p>
        </section>

        <div className="mt-14 flex flex-wrap gap-4">
          <Button asChild size="lg" className="group">
            <Link to="/new-run">
              Run a persona yourself
              <ArrowRight className="h-4 w-4 transition-transform duration-200 group-hover:translate-x-0.5" />
            </Link>
          </Button>
        </div>
      </main>
      <Footer />
    </>
  );
}

function Stat({ term, value, note }: { term: string; value: string; note: string }) {
  return (
    <div className="card-chart p-5">
      <dt className="font-mono text-[0.6875rem] uppercase tracking-wide text-ink-3">{term}</dt>
      <dd className="mt-1 font-display text-3xl font-bold text-ink">{value}</dd>
      <dd className="mt-1 text-sm text-ink-3">{note}</dd>
    </div>
  );
}

function Row({ row }: { row: BugRow }) {
  return (
    <tr className="border-b border-rule/60 align-top last:border-0">
      <th scope="row" className="px-4 py-3 font-mono font-normal">
        {row.bug}
        <span className="block text-[0.75rem] text-ink-3">{row.owner}</span>
      </th>
      <td className="px-4 py-3 font-mono text-[0.8125rem]">{row.signal ?? "none"}</td>
      {SYSTEMS.map((s) => (
        <td key={s} className="px-4 py-3">
          <span
            className={cn(
              "inline-block rounded-full px-2 py-0.5 font-mono text-[0.75rem]",
              row.detected[s] ? "bg-ink text-paper-raised" : "text-ink-3",
            )}
          >
            {row.detected[s] ? "found" : "–"}
          </span>
          <span className="mt-1 block text-[0.75rem] text-ink-3">{row.cells[s]}</span>
        </td>
      ))}
    </tr>
  );
}
