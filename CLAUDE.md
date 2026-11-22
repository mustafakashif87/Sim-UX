# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

# SimUX

LLM persona agents that attempt real tasks on web pages and report usability and accessibility failures grounded in Nielsen's heuristics and WCAG 2.2. FYP 2026–27, FAST-NUCES.

`docs/persona-design-spec.md` is the design authority: persona framework, interface contracts, seeded bugs, grounding pipeline, evaluation protocol, delivery and ownership. Read the relevant section before changing any module.

## Commands

Python 3.12 (CI uses the same). Members develop on macOS and Windows; CI runs the unit tests and the lefthook hooks on both Ubuntu and Windows, and `.gitattributes` keeps every text file LF.

```bash
python3.12 -m venv .venv && source .venv/bin/activate   # Windows: py -3.12 -m venv .venv; .venv\Scripts\activate
pip install -e ".[dev]"                 # add ,browser for Playwright
lefthook install                        # once per clone; installs commit and push hooks
ruff check . && ruff format --check .   # lint and format check, as CI runs them
pytest -q                               # unit tests (tests/e2e excluded by default)
pytest -q tests/test_contracts.py::TestFinding::test_valid   # one test
```

Browser tests need `pip install -e ".[dev,browser]"` and `playwright install --only-shell chromium`, then `pytest -q tests/e2e --override-ini addopts=` (plain `pytest` skips them). With the same extras, `python test-app/check_seeds.py` checks every seeded bug against `test-app/SEEDED_BUGS.md` and exits 1 on any mismatch. `python -m agent.run --page order-a --seed 1` runs P1 on one test-app page with the real model (key from `.env`) and prints intended vs executed actions and findings; add `--logs logs/demo --replay` to replay the recorded demo runs with no API call, `--headed` to show the browser. `python -m agent.demo` runs the whole mid-eval demo (four pages, live; `--replay` for the recording, `--from <page>` to continue, `--check` before presenting; live replies go to the git-ignored `logs/demo/live-cache/`, and only `--record` rewrites the recording). Its visible browser needs full Chromium: `playwright install chromium`, not only the shell. `--condition baseline` runs the same persona with every constraint off (full tree, every action, full memory, no perturbation, twice the steps). With `pip install -e ".[dev,browser,api]"`, `uvicorn api.app:app --port 8000` serves the API (`POST /runs`, `GET /runs/{id}`, `GET /runs/{id}/stream`, `GET /options`); see `api/README.md`.

Built so far: `agent/contracts.py`, `agent/perception.py` (snapshot to tree with refs, pure), `agent/actions.py` (action whitelist validator, pure), `agent/persona.py` (loads and validates `personas/*.yaml`: P1 `error_prone.yaml`, P2 `memoryless.yaml` and P3 `low_literacy.yaml` are built, and all 14 personas: P4 `screen_reader`, P5 `keyboard_only`, P6 `touch_imprecise`, P7 `low_vision_zoom`, P8 `skimmer`, P9 `interrupted`, P10 `slow_network`, P11 `help_seeker`, P12 `habitual`, P13 `power_user`, P14 `older_adult` (catalogue: `docs/persona-catalogue.md`); P3's `vocab_filter` uses NGSL 1.2 plus `personas/vocab/ui_allowlist.txt` through `agent/vocab.py`), `agent/perturb.py` (seeded mistakes between intent and execution), `agent/environment.py` (the Environment axis: device, viewport, text scale; network latency and failure are applied by the loop's `Server`), `agent/behaviour.py` (multi-step behaviours: page clock, think time and interruptions; P11's help escalation; P12's habit; P13's step budget and KLM time), `agent/loop.py` (one run: observe, model, validate, perturb, act, log, goal check), `agent/fake_model.py` (scripted model for tests), `agent/llm.py` (real model: one OpenAI-compatible client; `LLM_PROVIDER` groq, openrouter, gemini or ollama, `LLM_API_KEY`, optional `LLM_MODEL`, read from the shell or the git-ignored `.env`; retries 429 with backoff, record and replay by request hash, `ProviderError` ends a run as `aborted_provider`), `agent/detectors/` (read a run's logs, emit Findings; each run uses only its persona's detectors, by `source` in the signal map: P1's `data_loss_on_error`, `error_not_identified`, `error_not_actionable`, `duplicate_submission`, `destructive_without_confirm`, `no_way_back` and `redundant_entry`; P2's `recall_required`, `lost_location` (reads the page title the loop logs with each observation) and `no_progress_indicator`; P3's `label_unintelligible`, `instruction_unintelligible` and `system_language`; extension personas in `extension.py` (P4 to P8, P10) and `later.py` (P9, P11 to P13; P14 reuses others through the signal map's `also:`), reading the unfiltered tree and page facts their runs log; all deterministic; candidates, severity and confidence come from `grounding/`), `agent/keyboard_sweep.py` (no model: Tab through a page for `keyboard_trap` and `unreachable_control`, SB-04 and SB-05; `python -m agent.keyboard_sweep --page basket-a`), `agent/evaluate.py` (the evaluation protocol: every seeded bug of a persona × 3 conditions × N seeds into a resumable `runs.csv`, `summary.md` and `metrics.json`; `python -m agent.evaluate --persona error_prone --seeds 5 --out eval-out`, `--rescore` re-detects logged runs with no model; several keys as `LLM_PROVIDER_2`, `LLM_API_KEY_2`, `LLM_MODEL_2` and so on are switched automatically when one is spent, never mixing models within one evaluation folder: `agent/keypool.py`), `agent/metrics.py` (pure: k/n per condition, stable at 4/5, attribution, recall, precision, false-positive rate, trigger rate and detection given trigger, citation validity), `agent/compare.py` (the comparison table: SimUX, keyboard sweep, axe-core and a single-prompt LLM, one row per seeded bug), `agent/cli.py` (the `simux run` command: `.simux.yaml` in, `findings.json` out, exit 1 when a finding reaches `fail_on`; `action.yml` wraps it as a GitHub Action, self-tested on `examples/action-fixture/` by `action-selftest.yml`), `agent/run.py` (command line: one run on one page, then its findings with verified citations), `agent/ids.py` (run IDs), `agent/demo.py` (the mid-eval demo: four pages live or replayed, stops on a failure and names the next command), `agent/tasks.py` (`Task`, loads `test-app/tasks.yaml` and `SEEDED_BUGS.md`, `serve()` gives the test app over HTTP) and `agent/browser.py` (Playwright side: `observe`, `locate`, `act`), `api/` (FastAPI service over `agent.run`; runs in a worker thread, Playwright imported only when a run starts), plus `grounding/` (signal map, verbatim WCAG and Nielsen corpus, quote verification, rule-based severity; stub without retrieval). `web/` (the POC interface with its history: `npm ci && npm run dev` in `web/`; New Run starts a real run through the API and `/runs/:runId` streams it; the landing and fixture screens still read `useDemoRun()`). Other module folders hold a README naming purpose and owner. Add commands here as each module lands.

## CI/CD

`.github/workflows/`: `ci.yml` on every pull request and push to `main`; `cd.yml` after CI passes on `main`; `eval.yml` and `release.yml` on demand and on `v*` tags.

Each job switches on when its file appears, so these paths and behaviours are contracts:

| File | Switches on | Must |
| --- | --- | --- |
| `test-app/check_seeds.py` | CI `seeds` | exit non-zero when any page disagrees with the ground truth |
| `tests/e2e/test_*.py` | CI `e2e` (browser and end-to-end tests) | pass with real Chromium and the fake model; no API key. Fixture pages live in `tests/fixtures/pages/` |
| `test-app/*.html` | CI `axe` scan of the test app | nothing; violations are reported, never gating. The axe job's self-test on `.github/scripts/axe-fixture/` always runs and does gate |
| `web/package-lock.json` | CI `web` | `npm run build` succeeds |
| `test-app/index.html` | CD GitHub Pages deploy | contain a `<title>` (the post-deploy smoke check greps for it) |
| `api/Dockerfile` | CI `api-image` (build and `/health` smoke test); CD image push to ghcr.io | build from the repo root as context |
| `action.yml`, `examples/action-fixture/` | `action-selftest.yml` | the Action fails on order-a and passes on order-b |
| `agent/evaluate.py` | `eval.yml` | accept `--persona`, `--seeds`, `--out` and read `LLM_API_KEY` |

When a new CI job starts running, add it to `main`'s required status checks.

Local hooks: `lefthook.yml` runs ruff on staged Python files at commit and `pytest` at push. Each tool is skipped with a warning when not on `PATH`; CI stays the hard gate.

## Invariants

These hold across every module. A change that breaks one is wrong even if tests pass.

- **Constraints, not roleplay.** A persona's limits are enforced in harness code: perception filter, action whitelist, history window and step cap, perturbation layer. Test: delete the system prompt and the limits still hold. Put a new limit in the module that owns its axis, never in prompt text.
- **Accessibility tree only.** The model receives the filtered accessibility tree with harness-assigned refs (`e1`, `e2`…). Raw HTML, screenshots and the ref-to-locator map stay inside the harness. Read the tree with Playwright's `locator.aria_snapshot()`; pruned snapshots drop unnamed nodes, which are often the evidence.
- **Harness decides success.** Each task's goal check is evaluated by the harness after every action. The model can give up; it cannot declare success.
- **Intended and executed actions are logged separately** in every step record, so each perturbation is auditable. Behavioural bugs (a focus trap, a lost value) only show in step history, never in one snapshot.
- **Grounding is mapped, quoted and verified.** `grounding/signal_map.yaml` picks candidate criteria; the LLM only writes the justification. Every quote must be an exact substring of the corpus chunk, or the citation is dropped and the finding marked ungrounded. Corpus text is copied verbatim from the official source, with its URL.
- **Interface contracts are Pydantic models.** Observation, Action, Step record and Finding match the spec's shapes; change the spec and the model together.

## Test app and ground truth

- One ground-truth file in `test-app/` names every seeded bug. Page text, attributes, IDs, class names and anything reaching the accessibility tree stay neutral, so the agent gets no hints.
- Every seeded page has a buggy and a clean version that differ only in that bug.
- Raw run logs in `logs/` are append-only evidence; record corrections in a notes column, never by editing the log.

## Tests

Tests drive the agent with a scripted fake model: deterministic, offline, no API key. Real-model runs belong to the evaluation protocol (3 conditions × 5 seeds) and report every run as k/5, never the best run.

A new detector ships with a fixture pair: it fires on the buggy page and stays silent on the clean one.

## Workflow

- GitHub flow: `main` is protected; work on a short-lived branch (`feat/`, `fix/`, `test/`, `ci/`, `docs/`) and merge by pull request once CI passes (reviews welcome, not required).
- Keep each change small enough for its owner to explain line by line at the mid-eval.
