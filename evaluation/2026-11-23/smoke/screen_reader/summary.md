# Evaluation: screen_reader

Model: groq/openai/gpt-oss-120b. Every run is counted; k/n per condition.

| Bug | Signal | Persona on buggy | Baseline on buggy | Persona on clean | Triggered | Detected given trigger | Stable | Attributed |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| B13 | `status_not_announced` | 1/1 | 0/0 | 0/1 | 1/1 | 1/1 | yes | yes |
| B14 | `non_semantic_control` | 1/1 | 0/0 | 0/1 | 1/1 | 1/1 | yes | yes |
| B15 | `no_structure` | 0/1 | 0/0 | 0/1 | 1/1 | 0/1 | no | no |

- Runs: 8 (2 excluded: provider or harness failure)
- Recall, found (stable on buggy, silent on clean): 0.667 (2/3)
- Recall, attributed to the persona (baseline silent too): 0.667 (2/3)
- Precision (expected signal / all persona findings): 1.0
- False-positive rate (findings / clean runs): 0.0
- Citation validity (verified / generated quotes): 1.0
- Mean steps per run: 7.5; mean seconds: 74.18
