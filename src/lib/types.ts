// Shared types for the SimUX POC's fixture-data seam. This is the one
// place the eventual real API response shape should be modeled — see
// hooks/useDemoRun.ts, which is the single function every screen reads
// through. Swapping fixtures for a real backend later means changing
// that one hook's implementation, not these types or the screens that
// consume them.

export type Severity = "high" | "medium" | "low";

export type PersonaId = "accessibility" | "motor";

export interface Persona {
  id: PersonaId;
  name: string;
  /** Plain-language description of the actual restriction, not a roleplay
   *  instruction — see POC_SPEC.md rule 4 / the Agent Layer's real design
   *  intent (perceptual/action restriction, not "act as a persona"). */
  restriction: string;
}

export type TaskId = "signup" | "checkout";

export interface DemoTask {
  id: TaskId;
  label: string;
}

/** Named identically to the eventual LangGraph node names (see
 *  agent/graph.py in site-doctor, and POC_SPEC.md rule 4) so a real
 *  graph built later maps 1:1 onto what's already on screen. */
export type PipelineStage = "crawl" | "detect" | "ground" | "fix" | "sandbox" | "verify" | "aggregate";

export interface StageInfo {
  id: PipelineStage;
  label: string;
  description: string;
}

/** A citation must always be genuine, correctly-quoted WCAG or Nielsen
 *  text — hand-picked, never retrieved, never invented (POC_SPEC.md
 *  rule 3, the one non-negotiable rule in this whole project). Every
 *  citation object in fixtures/citations.ts carries a sourcing comment
 *  recording exactly where its text was verified against the live
 *  source, for the M12 re-check. */
export interface Citation {
  source: "WCAG" | "Nielsen";
  /** e.g. "WCAG 2.2 SC 4.1.2" or "Nielsen Heuristic #1" */
  id: string;
  title: string;
  /** Verbatim quoted text from the real source — never paraphrased. */
  text: string;
  url: string;
}

export interface FixWalkthrough {
  proposedFix: string;
  sandboxNote: string;
  verifyResult: "pass" | "fail";
}

export interface Finding {
  id: string;
  personaId: PersonaId;
  taskId: TaskId;
  severity: Severity;
  title: string;
  observation: string;
  recommendation: string;
  /** Present only when a real, verified citation backs this finding —
   *  never fabricated to fill the field. */
  citation?: Citation;
  /** Present only on the two confirmed showcase findings (one per
   *  full-depth persona) — see POC_SPEC.md §6 item 5. Every other
   *  finding is a plain card with no walkthrough. */
  showcase?: FixWalkthrough;
}

export interface UIScoreBreakdown {
  composite: number;
  visualDesign: number;
  accessibilityVisual: number;
}

export interface RunSummary {
  id: string;
  ranAt: string;
  uiScore: number;
  highCount: number;
  mediumCount: number;
  lowCount: number;
}

export interface DemoRun {
  productName: string;
  ranAt: string;
  personas: Persona[];
  tasks: DemoTask[];
  stages: StageInfo[];
  findings: Finding[];
  uiScore: UIScoreBreakdown;
  /** Prior runs only, most recent first — the current run above is not
   *  repeated in this list. Depicts the Aggregation Layer's regression/
   *  compare-over-time capability (POC_SPEC.md §6 item 4). */
  history: RunSummary[];
}
