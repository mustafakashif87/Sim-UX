# Evaluation: slow_network

Model: gemini/gemini-3.8-flash, groq/openai/gpt-oss-120b. Every run is counted; k/n per condition.

| Bug | Signal | Persona on buggy | Baseline on buggy | Persona on clean | Triggered | Detected given trigger | Stable | Attributed |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| B28 | `no_loading_feedback` | 1/1 | 0/0 | 0/1 | 1/1 | 1/1 | yes | no |
| B29 | `network_failure_silent` | 1/1 | 0/0 | 0/1 | 1/1 | 1/1 | yes | no |

- Runs: 8 (4 excluded: provider or harness failure)
- Recall, found (stable on buggy, silent on clean): 1.0 (2/2)
- Recall, attributed to the persona (baseline silent too): 0.0 (0/2)
- Precision (expected signal / all persona findings): 0.667
- False-positive rate (findings / clean runs): 0.0
- Citation validity (verified / generated quotes): 1.0
- Mean steps per run: 9.5; mean seconds: 51.7
