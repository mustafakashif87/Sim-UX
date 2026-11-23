# Evaluation results

Summaries of the real-model evaluation runs, one folder per date. Each
evaluation folder holds what `agent.evaluate` writes, without the raw logs:

- `summary.md`: the per-bug table and the headline metrics
- `metrics.json`: the same numbers, machine-readable
- `runs.csv`: one row per run (status, steps, signals, model, trigger)

The raw step logs (`runs/`) and model-reply caches (`llm-cache/`) stay with
whoever ran the evaluation; they are about 24 MB per full set. Re-scoring with
new detectors needs those logs: `python -m agent.evaluate ... --rescore`.

`run_evals.sh` reruns P2, P3 and the P4 to P14 smoke runs until done, waiting
out spent quotas.

## 2026-11-23

Every run used `groq/openai/gpt-oss-120b` at temperature 0, from `main` with
PRs #78 to #80. Kept runs exclude provider and harness failures.

| Folder | Persona | Protocol | Runs kept |
| --- | --- | --- | --- |
| `p1-error_prone` | P1 | 5 seeds × 3 conditions, plus `triggered_buggy` for B1 to B4 | 110 |
| `p2-memoryless` | P2 | 5 seeds × 3 conditions | 45 |
| `p3-low_literacy` | P3 | 5 seeds × 3 conditions | 45 |
| `smoke/<persona>` | P4 to P14 | 1 seed, `persona_buggy` and `persona_clean` only | 48 |
| `comparison` | all | `agent.compare`: SimUX, keyboard sweep, axe-core 4.10.2, single-prompt LLM | |

### Headline

| System | Seeded bugs detected |
| --- | --- |
| SimUX personas | 22 of the 36 persona bugs found; 2 of 12 strictly attributed (P1 to P3) |
| SimUX keyboard sweep | 3 of 41 (SB-04, SB-05, B14) |
| axe-core 4.10.2 | 5 of 41 (SB-01 to SB-03, B15, B16) |
| Single-prompt LLM | 5 of 41 (SB-01 to SB-03, B6, B11) |

False alarms: 1 in about 84 clean-page runs (P2). Citation validity: 100%.

### Read these numbers with care

- **`comparison.md`'s "Detected" total for SimUX (18) counts only attributed
  bugs, and it counts the smoke rows as attributed although their baseline was
  not run.** Quote "found" for the smoke rows, and use the figures above.
- **Smoke rows are one run each**, so "1/1" or "0/1" is weak evidence.
- **B1 to B4** are caught whenever P1's mistake reaches them (1 of 1 each);
  in `triggered_buggy`, B4 is caught 5 of 5. Report found, attributed and
  caught-when-triggered side by side.
- **B5, B6, B9 and B12** are found but not attributed: the no-limits
  baseline hits them too, so any user would.
- **`smoke/slow_network`** was re-scored with the detector fix from #80
  (a retry under an error already on screen is not "silent").
- Most misses are runs where the model finished the task before reaching the
  bug (B8, B10, B23 to B27, B34). The detectors fire on every bug in the
  browser tests when the bug is reached.
