# Evaluation: low_vision_zoom

Model: groq/openai/gpt-oss-120b. Every run is counted; k/n per condition.

| Bug | Signal | Persona on buggy | Baseline on buggy | Persona on clean | Triggered | Detected given trigger | Stable | Attributed |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| B20 | `reflow_failure` | 1/1 | 0/0 | 0/1 | 1/1 | 1/1 | yes | no |
| B21 | `focus_obscured` | 1/1 | 0/0 | 0/1 | 1/1 | 1/1 | yes | no |
| B22 | `text_clipped` | 1/1 | 0/0 | 0/1 | 1/1 | 1/1 | yes | no |

- Runs: 11 (5 excluded: provider or harness failure)
- Recall, found (stable on buggy, silent on clean): 1.0 (3/3)
- Recall, attributed to the persona (baseline silent too): 0.0 (0/3)
- Precision (expected signal / all persona findings): 1.0
- False-positive rate (findings / clean runs): 0.0
- Citation validity (verified / generated quotes): 1.0
- Mean steps per run: 9.0; mean seconds: 46.15
