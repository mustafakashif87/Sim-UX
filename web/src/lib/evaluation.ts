// The measured comparison: one row per seeded bug, as `agent.compare` writes
// it (evaluation/<date>/comparison/table.json, copied to src/data/). To
// refresh after a new evaluation, copy the new table.json over it.
import table from "@/data/evaluation.json";

export const SYSTEMS = ["simux", "keyboard_sweep", "axe", "single_prompt"] as const;
export type System = (typeof SYSTEMS)[number];

export const SYSTEM_LABEL: Record<System, string> = {
  simux: "SimUX personas",
  keyboard_sweep: "SimUX keyboard sweep",
  axe: "axe-core 4.10.2",
  single_prompt: "Single-prompt LLM",
};

export interface BugRow {
  bug: string;
  signal: string | null;
  owner: string;
  cells: Record<System, string>;
  detected: Record<System, boolean>;
}

export const ROWS = table as BugRow[];
export const EVALUATION_DATE = "23 Nov 2026 runs, rescored 25 Nov 2026";

export function detectedBy(system: System): number {
  return ROWS.filter((r) => r.detected[system]).length;
}

/** Found by SimUX at all: by a persona or by its own keyboard sweep. */
export const SIMUX_TOTAL = ROWS.filter((r) => r.detected.simux || r.detected.keyboard_sweep).length;
