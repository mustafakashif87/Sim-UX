# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

# SimUX

LLM persona agents that attempt real tasks on web pages and report usability and accessibility failures grounded in Nielsen's heuristics and WCAG 2.2. FYP 2026–27, FAST-NUCES.

`docs/persona-design-spec.md` is the design authority: persona framework, interface contracts, seeded bugs, grounding pipeline, evaluation protocol, delivery and ownership. Read the relevant section before changing any module.

## Current state

Skeleton only: each top-level folder has a README naming its purpose and owner, and no code exists yet. Add build, test and run commands to this file as each module lands.

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

- GitHub flow: `main` is protected; work on a short-lived branch (`feat/`, `fix/`, `test/`, `ci/`, `docs/`) and merge by pull request with one review.
- Keep each change small enough for its owner to explain line by line at the mid-eval.
