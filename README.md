# SimUX

[![CI](https://github.com/mustafakashif87/Sim-UX/actions/workflows/ci.yml/badge.svg)](https://github.com/mustafakashif87/Sim-UX/actions/workflows/ci.yml) [![CD](https://github.com/mustafakashif87/Sim-UX/actions/workflows/cd.yml/badge.svg)](https://github.com/mustafakashif87/Sim-UX/actions/workflows/cd.yml)

A multi-persona UI/UX auditor. LLM agents attempt real tasks on a web page under persona constraints enforced in code (what they perceive, what they can do, what they remember, and what goes wrong between intent and action), then report the failures they hit, grounded in Nielsen's 10 heuristics and WCAG 2.2.

FYP 2026–27, Department of AI & Data Science, FAST-NUCES. Supervisor: Ms. Saira Qamar.

## Status

Interface contracts (`agent/contracts.py`) with tests, and the full CI/CD pipeline, are in place; the other modules are still folders with a README. The mid-evaluation target is the persona framework with the Error-prone user (P1) built end to end, running live behind the web interface and delivered through GitHub CI/CD. See [`docs/persona-design-spec.md`](docs/persona-design-spec.md).

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
| `scripts/` | Development helpers (cross-platform git hooks) | All |

## Contributing

`main` changes only through pull requests. Branch from `main` with a prefix that names the work (`feat/`, `fix/`, `test/`, `docs/`, `ci/`), keep each pull request small, and get one review from another member before merging.

## CI/CD

| Workflow | Runs on | Does |
| --- | --- | --- |
| [`ci.yml`](.github/workflows/ci.yml) | Every pull request and push to `main` | Lint and unit tests; seeded-bug check, browser and end-to-end tests, web build and axe-core scan once those modules exist |
| [`cd.yml`](.github/workflows/cd.yml) | After CI passes on `main` | Deploys `test-app/` to GitHub Pages and smoke-checks the live URL; publishes the API image to ghcr.io |
| [`eval.yml`](.github/workflows/eval.yml) | Manual (Actions tab → Evaluation → Run workflow) | Runs the evaluation protocol with the real model; uploads logs as artifacts |
| [`release.yml`](.github/workflows/release.yml) | Pushing a `v*` tag | Creates a GitHub release with notes from merged pull requests |

Dependabot opens weekly pull requests for GitHub Actions and Python dependency updates.

**Local hooks (lefthook):** lefthook comes with the dev dependencies. Run once per clone:

```bash
# macOS / Linux
python3.12 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
lefthook install
```

```powershell
# Windows (PowerShell); needs Python 3.12 and Git for Windows
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
lefthook install
```

If PowerShell refuses to run `Activate.ps1`, run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` once.

Commits then auto-fix lint and formatting on staged Python files, and pushes run the tests first. CI still checks everything, so a skipped hook never lets a problem into `main`.

**One-time setup outside the repo**

- **Web (Vercel):** import this repository in Vercel with root directory `web/`. Vercel then deploys `main` to production and posts a preview URL on every pull request.
- **Evaluation:** add the `LLM_API_KEY` repository secret (Settings → Secrets and variables → Actions).
- **API host:** once chosen, point it at `ghcr.io/mustafakashif87/sim-ux-api:latest`.
- **Release:** `git tag v0.1-mid-eval && git push origin v0.1-mid-eval`.
