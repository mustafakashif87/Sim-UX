# Evaluation: error_prone

Model: groq/openai/gpt-oss-120b. Every run is counted; k/n per condition.

| Bug | Signal | Persona on buggy | Baseline on buggy | Persona on clean | Triggered | Detected given trigger | Stable | Attributed |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| B1 | `data_loss_on_error` | 1/5 | 0/5 | 0/5 | 1/5 | 1/1 | no | no |
| B2 | `error_not_identified` | 1/5 | 0/5 | 0/5 | 1/5 | 1/1 | no | no |
| B3 | `error_not_actionable` | 1/5 | 0/5 | 0/5 | 1/5 | 1/1 | no | no |
| B4 | `duplicate_submission` | 1/5 | 0/5 | 0/5 | 1/5 | 1/1 | no | no |
| B5 | `destructive_without_confirm` | 5/5 | 5/5 | 0/5 | 5/5 | 5/5 | yes | no |
| B6 | `redundant_entry` | 5/5 | 5/5 | 0/5 | 5/5 | 5/5 | yes | no |

Triggered condition (only the needed mistake made more frequent):

| Bug | Detected in triggered runs |
| --- | --- |
| B4 | 5/5 |

- Runs: 110 (0 excluded: provider or harness failure)
- Recall, found (stable on buggy, silent on clean): 0.333 (2/6)
- Recall, attributed to the persona (baseline silent too): 0.0 (0/6)
- Precision (expected signal / all persona findings): 0.933
- False-positive rate (findings / clean runs): 0.0
- Citation validity (verified / generated quotes): 1.0
- Mean steps per run: 3.85; mean seconds: 21.36
