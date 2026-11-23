# Evaluation: memoryless

Model: groq/openai/gpt-oss-120b. Every run is counted; k/n per condition.

| Bug | Signal | Persona on buggy | Baseline on buggy | Persona on clean | Triggered | Detected given trigger | Stable | Attributed |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| B7 | `recall_required` | 5/5 | 0/5 | 0/5 | 5/5 | 5/5 | yes | yes |
| B8 | `lost_location` | 0/5 | 0/5 | 0/5 | 5/5 | 0/5 | no | no |
| B9 | `no_progress_indicator` | 5/5 | 5/5 | 0/5 | 5/5 | 5/5 | yes | no |

- Runs: 46 (1 excluded: provider or harness failure)
- Recall, found (stable on buggy, silent on clean): 0.667 (2/3)
- Recall, attributed to the persona (baseline silent too): 0.333 (1/3)
- Precision (expected signal / all persona findings): 0.909
- False-positive rate (findings / clean runs): 0.067
- Citation validity (verified / generated quotes): 1.0
- Mean steps per run: 7.62; mean seconds: 28.9
