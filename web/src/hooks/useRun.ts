import { useEffect, useState } from "react";
import {
  ENDED,
  getOptions,
  getRun,
  streamRun,
  type Options,
  type RunSnapshot,
  type StepRecord,
} from "@/lib/api";

export interface LiveRun {
  /** null until the first answer from the API. */
  run: RunSnapshot | null;
  /** Steps in order, kept by step number (a reconnecting stream resends them). */
  steps: StepRecord[];
  error: string | null;
}

/**
 * One run, live: reads its snapshot, follows its stream while it runs,
 * then reads the snapshot again for the final run.json and findings.
 * Every screen about a real run reads it through this hook, as the POC's
 * screens read the fixture through useDemoRun.
 */
export function useRun(runId: string): LiveRun {
  const [run, setRun] = useState<RunSnapshot | null>(null);
  const [byStep, setByStep] = useState<Map<number, StepRecord>>(new Map());
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let stop: (() => void) | undefined;
    let cancelled = false;

    const keep = (steps: StepRecord[]) =>
      setByStep((prev) => {
        const next = new Map(prev);
        steps.forEach((s) => next.set(s.step, s));
        return next;
      });

    const refresh = () =>
      getRun(runId)
        .then((snap) => {
          if (cancelled) return;
          setRun(snap);
          keep(snap.steps);
        })
        .catch((e: Error) => !cancelled && setError(e.message));

    getRun(runId)
      .then((snap) => {
        if (cancelled) return;
        setRun(snap);
        keep(snap.steps);
        if (ENDED.has(snap.status)) return;
        stop = streamRun(runId, {
          onStep: (step) => keep([step]),
          onEnd: () => void refresh(),
        });
      })
      .catch((e: Error) => !cancelled && setError(e.message));

    return () => {
      cancelled = true;
      stop?.();
    };
  }, [runId]);

  const steps = [...byStep.values()].sort((a, b) => a.step - b.step);
  return { run, steps, error };
}

/** Personas, pages and conditions the API offers. */
export function useOptions(): { options: Options | null; error: string | null } {
  const [options, setOptions] = useState<Options | null>(null);
  const [error, setError] = useState<string | null>(null);
  useEffect(() => {
    getOptions()
      .then(setOptions)
      .catch((e: Error) => setError(e.message));
  }, []);
  return { options, error };
}
