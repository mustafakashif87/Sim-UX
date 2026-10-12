# agent

The harness. Each persona constraint axis is enforced in exactly one module.

| Module | Does |
| --- | --- |
| `contracts.py` | The four interface contracts as Pydantic models |
| `perception.py` | Accessibility snapshot to tree with refs; perception filters; the text the model reads |
| `browser.py` | Everything that touches Playwright: `observe`, `act`, `settle`, `goal_reached` |
| `actions.py` | Action axis: the persona's whitelist |
| `persona.py` | Loads and validates `personas/*.yaml` |
| `perturb.py` | Perturbation axis: seeded mistakes between intent and execution |
| `loop.py` | One run: observe, model, validate, perturb, act, log, goal check |
| `fake_model.py` | Scripted model for tests and the demo fallback |
| `tasks.py` | `Task`; loads `test-app/tasks.yaml` and `SEEDED_BUGS.md`; serves the test app over HTTP |
| `detectors/` | Read a run's logs and emit Findings, with candidates and severity from `grounding/` |

Owner: Person B. Spec: Persona framework.
