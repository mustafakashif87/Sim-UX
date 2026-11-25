import { useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { motion } from "motion/react";
import { ArrowRight, Check } from "lucide-react";
import { SiteNav } from "@/components/SiteNav";
import { Footer } from "@/components/Footer";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group";
import { useOptions } from "@/hooks/useRun";
import {
  API_URL,
  PERSONA_ORDER,
  PERSONAS,
  startRun,
  type Condition,
  type PersonaId,
} from "@/lib/api";
import { cn } from "@/lib/utils";
import { containerVariantsSlow, itemVariants, transition } from "@/lib/motion";

/**
 * New Run, live. Choose a persona, a seeded test-app page, a condition and
 * a seed; Start sends `POST /runs` and opens the run's live screen. The
 * personas, pages and conditions all come from the API (`GET /options`),
 * so a persona that cannot run yet (P3 until its word list is chosen) is
 * shown with the API's reason and cannot be picked.
 *
 * Single-select: a run is one persona on one page (spec: Live interface).
 * The proposal's multi-persona aggregate report comes in a later iteration.
 */

const SEEDS = [1, 2, 3, 4, 5];
type Source = "test-app" | "html" | "file" | "url";
// Roles the success check can match (agent.browser.goal_reached: role and name).
const GOAL_ROLES = ["heading", "alert", "status", "button", "link", "dialog"];
const MAX_HTML = 500_000;
// Catalogue order: P1 to P14 (the API lists them by file name).
const ORDER: PersonaId[] = PERSONA_ORDER;

export default function NewRun() {
  const navigate = useNavigate();
  const { options, error: optionsError } = useOptions();
  const [persona, setPersona] = useState<PersonaId>("error_prone");
  const [page, setPage] = useState("order-a");
  const [condition, setCondition] = useState<Condition>("persona");
  const [seed, setSeed] = useState("1");
  const [source, setSource] = useState<Source>("test-app");
  const [html, setHtml] = useState("");
  const [fileName, setFileName] = useState<string | null>(null);
  const [url, setUrl] = useState("");
  const [task, setTask] = useState("");
  const [goalRole, setGoalRole] = useState("heading");
  const [goalName, setGoalName] = useState("");
  const [starting, setStarting] = useState(false);
  const [startError, setStartError] = useState<string | null>(null);

  // Pages grouped by task: each task has a version A and B of one page.
  const tasks = useMemo(() => {
    const byTask = new Map<string, { text: string; pages: string[] }>();
    for (const p of options?.pages ?? []) {
      const entry = byTask.get(p.task) ?? { text: p.text, pages: [] };
      entry.pages.push(p.page);
      byTask.set(p.task, entry);
    }
    return [...byTask.entries()];
  }, [options]);

  const chosen = options?.personas.find((p) => p.id === persona);
  const seedNumber = seed.trim() === "" ? null : Number(seed);
  const seedValid = seedNumber === null || (Number.isInteger(seedNumber) && seedNumber >= 0);
  const own = source !== "test-app";
  const htmlReady = html.trim().length > 0 && html.length <= MAX_HTML;
  const sourceReady = !own
    ? Boolean(page)
    : Boolean(task.trim() && goalName.trim()) &&
      (source === "url" ? /^https?:\/\//.test(url.trim()) : htmlReady);
  const canStart = Boolean(options && chosen?.built && sourceReady && seedValid && !starting);
  const target = !own ? page : source === "url" ? url.trim() : (fileName ?? "your page");

  async function readFile(file: File | undefined) {
    if (!file) return;
    setFileName(file.name);
    setHtml(await file.text());
  }

  async function start() {
    setStarting(true);
    setStartError(null);
    try {
      const ownPage = {
        task: task.trim(),
        goal_role: goalRole,
        goal_name: goalName.trim(),
        ...(source === "url" ? { url: url.trim() } : { html }),
      };
      const { run_id } = await startRun({
        persona,
        condition,
        seed: seedNumber,
        ...(own ? ownPage : { page }),
      });
      navigate(`/runs/${run_id}`);
    } catch (e) {
      setStartError((e as Error).message);
      setStarting(false);
    }
  }

  return (
    <>
      <SiteNav variant="app" />
      <main className="container py-20 md:py-28">
        <motion.div initial="hidden" animate="visible" variants={containerVariantsSlow}>
          <motion.p variants={itemVariants} className="eyebrow-sans">
            New run
          </motion.p>
          <motion.h1 variants={itemVariants} className="mt-3 font-hero text-d1 text-ink">
            Choose who tests, and what.
          </motion.h1>
          <motion.p variants={itemVariants} className="mt-4 max-w-[58ch] text-ink-2">
            A real run: a language model attempts the task in a real browser, under the
            persona's limits, and SimUX reports what failed and what to change. Use a page from
            the seeded test app (each in a buggy version A and a clean version B), or your own.
          </motion.p>
        </motion.div>

        {optionsError && (
          <p role="alert" className="mt-10 max-w-[58ch] rounded-lg border border-critical/45 p-4 text-ink">
            {optionsError} The API address is <span className="font-mono">{API_URL}</span>.
          </p>
        )}
        {!options && !optionsError && <p className="mt-10 text-ink-3">Loading choices…</p>}

        {options && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={transition(0.6, 0.1)}
            className="mt-10 space-y-12"
          >
            <section aria-labelledby="persona-heading">
              <h2 id="persona-heading" className="font-display text-xl font-bold text-ink">
                Persona
              </h2>
              <ToggleGroup
                type="single"
                value={persona}
                onValueChange={(v) => v && setPersona(v as PersonaId)}
                className="mt-4 grid gap-5 md:grid-cols-3"
                aria-label="Persona"
              >
                {[...options.personas]
                  .sort((a, b) => ORDER.indexOf(a.id) - ORDER.indexOf(b.id))
                  .map((p) => (
                  <ToggleGroupItem key={p.id} value={p.id} disabled={!p.built} className="h-full">
                    <PersonaCard id={p.id} reason={p.reason} />
                  </ToggleGroupItem>
                ))}
              </ToggleGroup>
            </section>

            <section aria-labelledby="page-heading">
              <h2 id="page-heading" className="font-display text-xl font-bold text-ink">
                Task and page
              </h2>
              <ToggleGroup
                type="single"
                value={source}
                onValueChange={(v) => v && setSource(v as Source)}
                className="mt-4 flex flex-wrap gap-3"
                aria-label="Page source"
              >
                {(
                  [
                    ["test-app", "Seeded test app"],
                    ["html", "Paste HTML"],
                    ["file", "Upload .html"],
                    ...(options.own_page?.url ? [["url", "Web address"]] : []),
                  ] as [Source, string][]
                ).map(([value, label]) => (
                  <ToggleGroupItem
                    key={value}
                    value={value}
                    className="w-auto rounded-full border border-rule px-4 py-2 font-mono text-sm data-[state=on]:bg-ink data-[state=on]:text-paper-raised"
                  >
                    {label}
                  </ToggleGroupItem>
                ))}
              </ToggleGroup>

              {own && (
                <div className="mt-6 grid gap-6 md:grid-cols-2">
                  <div className="md:col-span-2">
                    {source === "html" && (
                      <>
                        <Label htmlFor="html">Your page&apos;s HTML</Label>
                        <textarea
                          id="html"
                          value={html}
                          onChange={(e) => setHtml(e.target.value)}
                          rows={10}
                          spellCheck={false}
                          placeholder="<!doctype html>"
                          className="mt-2 w-full rounded-lg border border-rule bg-paper-raised p-3 font-mono text-[0.8125rem] text-ink"
                        />
                      </>
                    )}
                    {source === "file" && (
                      <>
                        <Label htmlFor="file">An .html file</Label>
                        <Input
                          id="file"
                          type="file"
                          accept=".html,.htm,text/html"
                          onChange={(e) => readFile(e.target.files?.[0])}
                          className="mt-2"
                        />
                      </>
                    )}
                    {source === "url" && (
                      <>
                        <Label htmlFor="url">Public web address</Label>
                        <Input
                          id="url"
                          type="url"
                          value={url}
                          onChange={(e) => setUrl(e.target.value)}
                          placeholder="https://example.com/checkout"
                          className="mt-2"
                        />
                      </>
                    )}
                    {source !== "url" && (
                      <p className="mt-2 text-xs text-ink-3">
                        One self-contained page: inline CSS and scripts work. It runs offline, so
                        it cannot load anything from other sites.
                        {html.length > MAX_HTML && " This page is over the 500 KB limit."}
                      </p>
                    )}
                  </div>
                  <div className="md:col-span-2">
                    <Label htmlFor="task">Task, as a user would say it</Label>
                    <Input
                      id="task"
                      value={task}
                      onChange={(e) => setTask(e.target.value)}
                      placeholder="Sign up with the name Sam Lee and the email sam@example.com"
                      className="mt-2"
                    />
                  </div>
                  <div>
                    <Label htmlFor="goal-role">Done when the page shows a</Label>
                    <select
                      id="goal-role"
                      value={goalRole}
                      onChange={(e) => setGoalRole(e.target.value)}
                      className="mt-2 h-10 w-full rounded-lg border border-rule bg-paper-raised px-3 font-mono text-sm text-ink"
                    >
                      {GOAL_ROLES.map((r) => (
                        <option key={r} value={r}>
                          {r}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <Label htmlFor="goal-name">with exactly this text</Label>
                    <Input
                      id="goal-name"
                      value={goalName}
                      onChange={(e) => setGoalName(e.target.value)}
                      placeholder="Account created"
                      className="mt-2"
                    />
                  </div>
                  <p className="text-xs text-ink-3 md:col-span-2">
                    The harness, not the model, decides success: the run succeeds only when that
                    element is visible. Your page has no answer key, so you get findings and fixes,
                    not a recall score.
                  </p>
                </div>
              )}

              <div className={cn("mt-4 grid gap-3 md:grid-cols-2", own && "hidden")}>
                {tasks.map(([task, { text, pages }]) => (
                  <fieldset key={task} className="rounded-xl border border-rule p-4">
                    <legend className="px-1 font-mono text-[0.75rem] uppercase tracking-wide text-ink-3">
                      {task}
                    </legend>
                    <p className="text-[0.9375rem] text-ink-2">{text}</p>
                    <div className="mt-3 flex gap-4">
                      {pages.map((name) => (
                        <label key={name} className="flex items-center gap-2 font-mono text-sm text-ink">
                          <input
                            type="radio"
                            name="page"
                            value={name}
                            checked={page === name}
                            onChange={() => setPage(name)}
                          />
                          {name}
                        </label>
                      ))}
                    </div>
                  </fieldset>
                ))}
              </div>
            </section>

            <section aria-labelledby="condition-heading" className="grid gap-8 md:grid-cols-2">
              <div>
                <h2 id="condition-heading" className="font-display text-xl font-bold text-ink">
                  Condition
                </h2>
                <ToggleGroup
                  type="single"
                  value={condition}
                  onValueChange={(v) => v && setCondition(v as Condition)}
                  className="mt-4 flex gap-3"
                  aria-label="Condition"
                >
                  {options.conditions.map((c) => (
                    <ToggleGroupItem
                      key={c}
                      value={c}
                      className="w-auto rounded-full border border-rule px-4 py-2 font-mono text-sm data-[state=on]:bg-ink data-[state=on]:text-paper-raised"
                    >
                      {c === "persona" ? "Persona limits on" : "Baseline: limits off"}
                    </ToggleGroupItem>
                  ))}
                </ToggleGroup>
                <p className="mt-2 text-xs text-ink-3">
                  The baseline runs the same persona with full view, full memory, no injected
                  mistakes and twice the steps, to show the limit caused a failure.
                </p>
              </div>
              <div className="max-w-xs">
                <Label htmlFor="seed">Seed</Label>
                <Input
                  id="seed"
                  inputMode="numeric"
                  list="seeds"
                  value={seed}
                  onChange={(e) => setSeed(e.target.value)}
                  aria-invalid={!seedValid}
                  className="mt-2"
                />
                <datalist id="seeds">
                  {SEEDS.map((s) => (
                    <option key={s} value={s} />
                  ))}
                </datalist>
                <p className="mt-2 text-xs text-ink-3">
                  Fixes which mistakes the persona makes. The evaluation uses seeds 1 to 5; empty
                  uses the persona's own.
                </p>
              </div>
            </section>
          </motion.div>
        )}

        <div className="mt-12 flex flex-wrap items-center gap-4">
          <Button size="lg" className="group" disabled={!canStart} onClick={start}>
            {starting ? "Starting…" : `Start ${condition === "baseline" ? "baseline" : "run"} on ${target}`}
            <ArrowRight className="h-4 w-4 transition-transform duration-200 group-hover:translate-x-0.5" />
          </Button>
          {startError && (
            <p role="alert" className="text-sm text-[hsl(var(--critical-ink))]">
              {startError}
            </p>
          )}
        </div>
      </main>
      <Footer />
    </>
  );
}

function PersonaCard({ id, reason }: { id: PersonaId; reason: string | null }) {
  const info = PERSONAS[id] ?? { code: "", name: id, axis: "", restriction: "", core: false };
  return (
    <div
      className={cn(
        "card-chart-lg relative flex h-full flex-col p-6 text-left transition-all duration-200",
        "group-data-[state=on]:ring-2 group-data-[state=on]:ring-ink group-data-[state=on]:ring-offset-2 group-data-[state=on]:ring-offset-paper",
        "group-disabled:opacity-60",
      )}
    >
      <span
        aria-hidden="true"
        className="absolute right-4 top-4 hidden h-6 w-6 place-items-center rounded-full bg-ink text-paper-raised group-data-[state=on]:grid"
      >
        <Check className="h-3.5 w-3.5" strokeWidth={3} />
      </span>
      <p className="font-mono text-[0.75rem] uppercase tracking-wide text-ink-3">
        {info.code} · {info.axis}
      </p>
      <h3 className="mt-1 pr-8 font-display text-lg font-bold tracking-tight text-ink">{info.name}</h3>
      <p className="mt-3 text-[0.9375rem] leading-relaxed text-ink-2">{info.restriction}</p>
      {reason && <p className="mt-3 text-xs text-ink-3">Not runnable yet: {reason}.</p>}
    </div>
  );
}
