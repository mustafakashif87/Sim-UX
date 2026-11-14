import { demoRun } from "@/lib/fixtures/demoRun";
import type { DemoRun } from "@/lib/types";

/**
 * The ONE seam between fixture data and every screen (POC_SPEC.md rule
 * 4). Every component reads run data through this hook, never by
 * importing `demoRun` directly — so when FYP-II wires in a real
 * backend, only this file's implementation changes (e.g. to a real
 * fetch + loading/error state), and no screen needs touching.
 *
 * Deliberately synchronous and side-effect-free for now: this POC makes
 * zero backend calls at runtime (POC_SPEC.md rule 1), so there is no
 * loading state to model yet. A real version would return
 * `{ data, isLoading, error }`; keep that shape in mind if this hook's
 * signature needs to grow later, but don't build it prematurely now.
 */
export function useDemoRun(): DemoRun {
  return demoRun;
}
