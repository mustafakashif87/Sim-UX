# SimUX

A multi-persona UI/UX auditor. LLM agents attempt real tasks on a web page under persona constraints enforced in code (what they perceive, what they can do, what they remember, and what goes wrong between intent and action), then report the failures they hit, grounded in Nielsen's 10 heuristics and WCAG 2.2.

FYP 2026–27, Department of AI & Data Science, FAST-NUCES. Supervisor: Ms. Saira Qamar.

## Status

Repository skeleton. The mid-evaluation target is the persona framework with the Error-prone user (P1) built end to end, running live behind the web interface and delivered through GitHub CI/CD. See [`docs/persona-design-spec.md`](docs/persona-design-spec.md).

## Repository layout

| Path | What | Owner |
| --- | --- | --- |
| `agent/` | Harness: perception filter, action validator, perturbation layer, agent loop, detectors | Person B |
| `personas/` | One YAML constraint config per persona | Person B |
| `api/` | FastAPI service that starts runs, streams steps and returns findings | Person B |
| `grounding/` | Signal-to-criterion map, corpus entries, citation verification | Person C |
| `web/` | Web interface (from the proposal POC) | Person C |
| `test-app/` | Seeded-bug test pages, buggy and clean versions | Person A |
| `tests/` | pytest suite driven by a scripted fake model | Person B |
| `logs/` | Evaluation run logs | Person A |
| `docs/` | Design spec and project documentation | All |

## Contributing

`main` changes only through pull requests. Branch from `main` with a prefix that names the work (`feat/`, `fix/`, `test/`, `docs/`, `ci/`), keep each pull request small, and get one review from another member before merging.
