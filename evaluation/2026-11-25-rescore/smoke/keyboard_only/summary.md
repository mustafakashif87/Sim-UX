# Evaluation: keyboard_only

Model: gemini/gemini-3.8-flash, groq/openai/gpt-oss-120b. Every run is counted; k/n per condition.

| Bug | Signal | Persona on buggy | Baseline on buggy | Persona on clean | Triggered | Detected given trigger | Stable | Attributed |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| B16 | `focus_order_illogical` | 0/1 | 0/0 | 0/1 | 1/1 | 0/1 | no | no |
| B17 | `focus_not_visible` | 1/1 | 0/0 | 0/1 | 1/1 | 1/1 | yes | no |

- Runs: 14 (10 excluded: provider or harness failure)
- Recall, found (stable on buggy, silent on clean): 0.5 (1/2)
- Recall, attributed to the persona (baseline silent too): 0.0 (0/2)
- Precision (expected signal / all persona findings): 0.5
- False-positive rate (findings / clean runs): 0.0
- Citation validity (verified / generated quotes): 1.0
- Mean steps per run: 19.75; mean seconds: 131.55
