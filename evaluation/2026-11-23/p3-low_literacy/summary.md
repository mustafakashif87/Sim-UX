# Evaluation: low_literacy

Model: groq/openai/gpt-oss-120b. Every run is counted; k/n per condition.

| Bug | Signal | Persona on buggy | Baseline on buggy | Persona on clean | Triggered | Detected given trigger | Stable | Attributed |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| B10 | `label_unintelligible` | 0/5 | 0/5 | 0/5 | 5/5 | 0/5 | no | no |
| B11 | `instruction_unintelligible` | 5/5 | 0/5 | 0/5 | 5/5 | 5/5 | yes | yes |
| B12 | `system_language` | 5/5 | 5/5 | 0/5 | 5/5 | 5/5 | yes | no |

- Runs: 48 (3 excluded: provider or harness failure)
- Recall, found (stable on buggy, silent on clean): 0.667 (2/3)
- Recall, attributed to the persona (baseline silent too): 0.333 (1/3)
- Precision (expected signal / all persona findings): 1.0
- False-positive rate (findings / clean runs): 0.0
- Citation validity (verified / generated quotes): 1.0
- Mean steps per run: 6.29; mean seconds: 60.92
