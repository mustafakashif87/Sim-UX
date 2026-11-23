# Evaluation: touch_imprecise

Model: gemini/gemini-3.8-flash, groq/openai/gpt-oss-120b. Every run is counted; k/n per condition.

| Bug | Signal | Persona on buggy | Baseline on buggy | Persona on clean | Triggered | Detected given trigger | Stable | Attributed |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| B18 | `mis_tap_consequence` | 1/1 | 0/0 | 0/1 | 1/1 | 1/1 | yes | yes |
| B19 | `target_too_small` | 1/1 | 0/0 | 0/1 | 1/1 | 1/1 | yes | yes |

- Runs: 7 (3 excluded: provider or harness failure)
- Recall, found (stable on buggy, silent on clean): 1.0 (2/2)
- Recall, attributed to the persona (baseline silent too): 1.0 (2/2)
- Precision (expected signal / all persona findings): 0.5
- False-positive rate (findings / clean runs): 0.0
- Citation validity (verified / generated quotes): 1.0
- Mean steps per run: 3.25; mean seconds: 5.95
