# Evaluation: error_prone

Model: groq/openai/gpt-oss-120b. Every run is counted; k/n per condition.

| Bug | Signal | Persona on buggy | Baseline on buggy | Persona on clean | Triggered | Detected given trigger | Stable | Attributed |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| B1 | `data_loss_on_error` | 2/5 | 0/5 | 0/5 | 2/5 | 2/2 | no | no |
| B2 | `error_not_identified` | 1/5 | 0/5 | 0/5 | 1/5 | 1/1 | no | no |
| B3 | `error_not_actionable` | 2/5 | 0/5 | 0/5 | 2/5 | 2/2 | no | no |
| B4 | `duplicate_submission` | 1/5 | 0/5 | 0/5 | 1/5 | 1/1 | no | no |

- Runs: 60 (0 excluded: provider or harness failure)
- Recall, found (stable on buggy, silent on clean): 0.0 (0/4)
- Recall, attributed to the persona (baseline silent too): 0.0 (0/4)
- Precision (expected signal / all persona findings): 1.0
- False-positive rate (findings / clean runs): 0.0
- Citation validity (verified / generated quotes): 1.0
- Mean steps per run: 2.98; mean seconds: 13.45
