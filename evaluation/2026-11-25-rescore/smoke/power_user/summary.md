# Evaluation: power_user

Model: gemini/gemini-3.8-flash, groq/openai/gpt-oss-120b. Every run is counted; k/n per condition.

| Bug | Signal | Persona on buggy | Baseline on buggy | Persona on clean | Triggered | Detected given trigger | Stable | Attributed |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| B34 | `no_enter_submit` | 0/1 | 0/0 | 0/1 | 1/1 | 0/1 | no | no |
| B35 | `no_bulk_action` | 1/1 | 0/0 | 0/1 | 1/1 | 1/1 | yes | no |

- Runs: 8 (4 excluded: provider or harness failure)
- Recall, found (stable on buggy, silent on clean): 0.5 (1/2)
- Recall, attributed to the persona (baseline silent too): 0.0 (0/2)
- Precision (expected signal / all persona findings): 0.5
- False-positive rate (findings / clean runs): 0.0
- Citation validity (verified / generated quotes): 1.0
- Mean steps per run: 3.5; mean seconds: 19.8
