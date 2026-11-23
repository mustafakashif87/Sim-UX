# Evaluation: interrupted

Model: gemini/gemini-3.8-flash, groq/openai/gpt-oss-120b. Every run is counted; k/n per condition.

| Bug | Signal | Persona on buggy | Baseline on buggy | Persona on clean | Triggered | Detected given trigger | Stable | Attributed |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| B26 | `timeout_no_warning` | 0/1 | 0/0 | 0/1 | 1/1 | 0/1 | no | no |
| B27 | `state_lost_on_reload` | 0/1 | 0/0 | 0/1 | 1/1 | 0/1 | no | no |

- Runs: 8 (4 excluded: provider or harness failure)
- Recall, found (stable on buggy, silent on clean): 0.0 (0/2)
- Recall, attributed to the persona (baseline silent too): 0.0 (0/2)
- Precision (expected signal / all persona findings): n/a
- False-positive rate (findings / clean runs): 0.0
- Citation validity (verified / generated quotes): n/a
- Mean steps per run: 6.0; mean seconds: 21.6
