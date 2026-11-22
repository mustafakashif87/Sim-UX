// The SimUX API client and the shapes it returns. These types mirror the
// Python contracts (agent/contracts.py) and the API (api/app.py); change
// them together. The landing page's showcase still reads the fixture types
// in lib/types.ts; everything about a real run comes from here.

/** Base URL of the API. Set VITE_SIMUX_API_URL at build time (Vercel: a
 *  project environment variable); local development uses port 8000. */
export const API_URL = (import.meta.env.VITE_SIMUX_API_URL ?? "http://localhost:8000").replace(
  /\/+$/,
  "",
);

/** The three personas of the spec, by config ID (personas/*.yaml). */
export type PersonaId =
  | "error_prone"
  | "memoryless"
  | "low_literacy"
  | "screen_reader"
  | "keyboard_only"
  | "touch_imprecise"
  | "low_vision_zoom"
  | "skimmer"
  | "interrupted"
  | "slow_network"
  | "help_seeker"
  | "habitual"
  | "power_user"
  | "older_adult";
export type Condition = "persona" | "baseline";

/** How the loop ended (agent.loop.RunStatus), or `failed` when the run
 *  broke before the loop could log anything. */
export type EndStatus =
  | "succeeded"
  | "gave_up"
  | "step_cap"
  | "aborted_provider"
  | "crashed"
  | "failed";
export type RunStatus = "queued" | "running" | EndStatus;

export const ENDED: ReadonlySet<RunStatus> = new Set<RunStatus>([
  "succeeded",
  "gave_up",
  "step_cap",
  "aborted_provider",
  "crashed",
  "failed",
]);

export type ActionKind = "click" | "type" | "press" | "scroll" | "back" | "give_up";

export interface Action {
  thought: string;
  action: ActionKind;
  ref: string | null;
  text: string | null;
  key: string | null;
}

/** One line of steps.jsonl: what the model intended and what reached the
 *  browser after perturbation (null when a perturbation dropped it). */
export interface StepRecord {
  run_id: string;
  persona: string;
  page: string;
  step: number;
  observation_hash: string;
  intended_action: Action;
  executed_action: Action | null;
  perturbation: string | null;
  result: "ok" | "invalid" | "error";
  goal_reached: boolean;
}

export interface Citation {
  source: "WCAG" | "Nielsen";
  criterion_id: string;
  /** Verbatim from the corpus; the harness checked it is an exact substring. */
  quote: string;
}

/** A detector's finding after grounding. No citations means ungrounded:
 *  still reported, at lower confidence, never hidden. */
export interface Finding {
  finding_id: string;
  persona: string;
  page: string;
  signal: string;
  evidence_steps: number[];
  candidate_criteria: string[];
  citations: Citation[];
  /** Nielsen's scale: 4 task blocked; 3 completed with data loss or over
   *  twice the shortest path; 2 recoverable friction; 1 cosmetic. */
  severity: 1 | 2 | 3 | 4;
  confidence: number;
  baseline_reproduced: boolean;
}

export interface RunRequest {
  persona: PersonaId;
  page: string;
  condition: Condition;
  seed: number | null;
}

/** run.json, as the loop writes it. Only the fields the interface reads. */
export interface RunMeta {
  run_id: string;
  persona: string;
  condition?: Condition;
  page: string;
  seed: number;
  model_id: string;
  status?: EndStatus;
  steps?: number;
  error?: string;
  replay?: boolean;
}

export interface RunSnapshot {
  run_id: string;
  status: RunStatus;
  request: RunRequest | null;
  error: string | null;
  meta: RunMeta | null;
  steps: StepRecord[];
  findings: Finding[];
}

export interface PersonaOption {
  id: PersonaId;
  max_steps: number;
  history_turns: number;
  built: boolean;
  reason: string | null;
}

export interface PageOption {
  page: string;
  task: string;
  text: string;
}

export interface Options {
  personas: PersonaOption[];
  pages: PageOption[];
  conditions: Condition[];
}

export class ApiError extends Error {
  constructor(
    readonly status: number,
    message: string,
  ) {
    super(message);
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${API_URL}${path}`, {
      ...init,
      headers: { "Content-Type": "application/json", ...init?.headers },
    });
  } catch {
    throw new ApiError(0, `Cannot reach the SimUX API at ${API_URL}. Is it running?`);
  }
  const body = await response.json().catch(() => null);
  if (!response.ok) {
    const detail = body?.detail;
    const message =
      typeof detail === "string"
        ? detail
        : Array.isArray(detail)
          ? detail.map((d: { msg?: string }) => d.msg).join("; ")
          : `${response.status} ${response.statusText}`;
    throw new ApiError(response.status, message);
  }
  return body as T;
}

export const getOptions = () => request<Options>("/options");

export const startRun = (req: RunRequest) =>
  request<{ run_id: string; status: RunStatus }>("/runs", {
    method: "POST",
    body: JSON.stringify(req),
  });

export const getRun = (runId: string) => request<RunSnapshot>(`/runs/${encodeURIComponent(runId)}`);

export interface StreamEnd {
  status: EndStatus;
  error: string | null;
  findings: Finding[];
}

/** Follow a run's steps as the loop writes them. Returns a function that
 *  stops listening. A reconnecting stream resends every step from the
 *  start, so callers keep steps by their number, not by arrival. */
export function streamRun(
  runId: string,
  handlers: { onStep: (step: StepRecord) => void; onEnd: (end: StreamEnd) => void },
): () => void {
  const source = new EventSource(`${API_URL}/runs/${encodeURIComponent(runId)}/stream`);
  source.addEventListener("step", (e) => handlers.onStep(JSON.parse((e as MessageEvent).data)));
  source.addEventListener("end", (e) => {
    source.close();
    handlers.onEnd(JSON.parse((e as MessageEvent).data));
  });
  return () => source.close();
}

/** What each persona is, in the spec's and catalogue's words: a limit
 *  enforced in code, never a character in a prompt. P1 to P3 are the core,
 *  evaluated in full; P4 to P14 are the extension (docs/persona-catalogue.md). */
export interface PersonaInfo {
  code: string;
  name: string;
  axis: string;
  restriction: string;
  core: boolean;
}

export const PERSONAS: Record<PersonaId, PersonaInfo> = {
  error_prone: {
    code: "P1",
    name: "Error-prone user",
    axis: "Perturbation",
    restriction:
      "Makes seeded slips between intent and action: typos, skipped fields, double presses and a stray Back.",
    core: true,
  },
  memoryless: {
    code: "P2",
    name: "Memoryless first-time user",
    axis: "Memory",
    restriction: "Sees only the current page. Nothing from earlier steps is remembered.",
    core: true,
  },
  low_literacy: {
    code: "P3",
    name: "Low-literacy or non-native reader",
    axis: "Perception",
    restriction:
      "Any word outside the 2,809 most common English headwords (NGSL) reads as [unknown].",
    core: true,
  },
  screen_reader: {
    code: "P4",
    name: "Screen-reader user",
    axis: "Perception and actions",
    restriction:
      "Reads about 15 items at a time in reading order, with a headings and landmarks list, and can only operate real controls.",
    core: false,
  },
  keyboard_only: {
    code: "P5",
    name: "Keyboard-only user",
    axis: "Actions and perception",
    restriction:
      "Keys only, no mouse. Where focus is invisible, it does not know where it is.",
    core: false,
  },
  touch_imprecise: {
    code: "P6",
    name: "Mobile touch user",
    axis: "Environment and perturbation",
    restriction:
      "On a phone; taps on small targets can land on a neighbour or miss, more often the smaller the target.",
    core: false,
  },
  low_vision_zoom: {
    code: "P7",
    name: "Low-vision magnifier user",
    axis: "Environment and perception",
    restriction: "400% zoom with text at 200%: sees only what fits in a 320 by 256 window.",
    core: false,
  },
  skimmer: {
    code: "P8",
    name: "Skimmer",
    axis: "Perception and budget",
    restriction:
      "Reads above the fold and the first 8 words of any text, with 10 steps to finish.",
    core: false,
  },
  interrupted: {
    code: "P9",
    name: "Interrupted user",
    axis: "Environment and memory",
    restriction:
      "Leaves for 15 minutes, comes back to a reloaded page, and remembers nothing from before.",
    core: false,
  },
  slow_network: {
    code: "P10",
    name: "Slow-connection user",
    axis: "Environment and perturbation",
    restriction:
      "Every submission takes 3 seconds and one in five fails; presses again when nothing seems to happen.",
    core: false,
  },
  help_seeker: {
    code: "P11",
    name: "Help-seeker",
    axis: "Actions",
    restriction: "Once stuck, can only look for help, contact or FAQ until it finds some.",
    core: false,
  },
  habitual: {
    code: "P12",
    name: "Habitual returning user",
    axis: "Memory and perturbation",
    restriction:
      "Remembers where it clicked last time, and sometimes clicks there again out of habit.",
    core: false,
  },
  power_user: {
    code: "P13",
    name: "Expert power user",
    axis: "Budget",
    restriction: "Has one and a half times the shortest path in steps, and expects Enter to work.",
    core: false,
  },
  older_adult: {
    code: "P14",
    name: "Older adult (composite)",
    axis: "Several at once",
    restriction:
      "Slower steps, larger text, the visible screen only, and less precise taps, all together.",
    core: false,
  },
};

/** P1 to P14 in order. */
export const PERSONA_ORDER = Object.keys(PERSONAS) as PersonaId[];

/** The spec's severity scale mapped onto the interface's three tags. */
export function severityTag(severity: Finding["severity"]): "high" | "medium" | "low" {
  return severity >= 3 ? "high" : severity === 2 ? "medium" : "low";
}
