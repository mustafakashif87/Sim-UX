"""`simux`: audit your own pages from the command line or CI (PA-10).

    simux run                       # reads .simux.yaml, writes findings.json
    simux run --config ci/.simux.yaml --out out/findings.json

`.simux.yaml` names the pages, a task for each and the persona:

    persona: error_prone        # a personas/*.yaml id
    seeds: [1, 2, 3]            # one run per page per seed
    fail_on: 2                  # exit 1 when any finding has this severity or more
    serve: site/                # optional: serve this folder; page urls are relative to it
    pages:
      - url: order.html
        task: Place the order for the kettle in your basket.
        goal: {role: heading, name: Order placed}
        endpoint: "**/api/orders"   # optional: answered with 200 by the harness

The model comes from LLM_PROVIDER / LLM_API_KEY / LLM_MODEL as in agent.llm.
For tests only, `model: {script: [...]}` drives a scripted fake model
(`{click: "Place order"}`, `{type: ["Email", "a@b.c"]}`) and
`perturbation: {...}` replaces the persona's rates (any not listed are 0).

findings.json holds every finding with its citations, plus each run's status,
so a CI step can show them. The exit code is 1 when a finding reaches
`fail_on`, 2 when every run failed for reasons outside the page (provider or
harness), else 0.
"""

import argparse
import json
import sys
import tempfile
from contextlib import nullcontext
from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, Field

from agent.contracts import Finding

CONFIG_FILE = ".simux.yaml"


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class GoalConfig(_Strict):
    role: str
    name: str


class PageConfig(_Strict):
    url: str
    task: str = Field(min_length=1)
    goal: GoalConfig
    endpoint: str | None = None


class Config(_Strict):
    persona: str = "error_prone"
    seeds: list[int] = Field(default=[1], min_length=1)
    fail_on: int = Field(default=2, ge=1, le=4)
    serve: str | None = None
    pages: list[PageConfig] = Field(min_length=1)
    model: dict | None = None  # {script: [...]} for tests
    perturbation: dict | None = None  # rate overrides for tests


def load_config(path: Path) -> Config:
    return Config.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")))


def _script_model(script: list[dict]):
    from agent.fake_model import FakeModel, click, press, type_into

    steps = []
    for entry in script:
        ((kind, value),) = entry.items()
        match kind:
            case "click":
                steps.append(click(value))
            case "type":
                steps.append(type_into(value[0], value[1]))
            case "press":
                steps.append(press(value))
            case _:
                raise ValueError(f"unknown script step {kind!r}")
    return FakeModel(steps)


def audit_pages(
    config: Config, base_dir: Path, logs: Path, browser=None
) -> tuple[list[Finding], list[dict], list[dict]]:
    """Findings, runs and findings as change requests (agent.report), for
    every page and seed; Chromium is launched unless `browser` is given
    (tests share one)."""
    from agent.persona import Persona, load_persona
    from agent.tasks import serve

    persona = load_persona(config.persona)
    if config.perturbation:
        data = persona.model_dump()
        data["perturbation"] = {"seed": data["perturbation"]["seed"], **config.perturbation}
        persona = Persona.model_validate(data)
    llm = None
    if config.model is None:
        from agent.llm import LLMClient

        llm = LLMClient.from_env(cache_dir=logs / "llm-cache")

    served = serve(base_dir / config.serve) if config.serve else nullcontext("")
    with served as root:
        if browser is not None:
            return _audit(config, base_dir, logs, persona, llm, root, browser)
        from playwright.sync_api import sync_playwright

        with sync_playwright() as p:
            launched = p.chromium.launch()
            try:
                return _audit(config, base_dir, logs, persona, llm, root, launched)
            finally:
                launched.close()


def _audit(config, base_dir, logs, persona, llm, root, browser):
    from agent.detectors import audit
    from agent.loop import run
    from agent.report import explain
    from agent.tasks import Goal, Task

    findings: list[Finding] = []
    changes: list[dict] = []
    runs: list[dict] = []
    for i, entry in enumerate(config.pages):
        if "://" in entry.url:
            url = entry.url
        elif root:
            url = root + entry.url
        else:
            url = (base_dir / entry.url).resolve().as_uri()
        goal = Goal(entry.goal.role, entry.goal.name)
        task = Task(f"page{i}", url, entry.task, goal, entry.endpoint)
        for seed in config.seeds:
            model = llm or _script_model(config.model["script"])
            page = browser.new_page()
            try:
                result = run(page, task, persona, model, logs, seed)
            finally:
                page.close()
            found = audit(result.log_dir)
            findings += found
            changes += explain(found, result.log_dir)
            runs.append(
                {
                    "url": entry.url,
                    "seed": seed,
                    "run_id": result.run_id,
                    "status": result.status,
                    "steps": len(result.steps),
                    "signals": [f.signal for f in found],
                }
            )
    return findings, runs, changes


def summary_markdown(findings: list[Finding], runs: list[dict], fail_on: int) -> str:
    lines = ["## SimUX findings", ""]
    if not findings:
        lines.append(f"No findings in {len(runs)} run(s).")
    else:
        lines += [
            "| Page | Signal | Severity | Criteria | Evidence steps |",
            "| --- | --- | --- | --- | --- |",
        ]
        for f in sorted(findings, key=lambda f: -f.severity):
            mark = " (fails)" if f.severity >= fail_on else ""
            lines.append(
                f"| {f.page} | `{f.signal}` | {f.severity}{mark} | "
                f"{', '.join(f.candidate_criteria)} | {f.evidence_steps} |"
            )
    lines += ["", "| Page | Seed | Status | Steps |", "| --- | --- | --- | --- |"]
    lines += [f"| {r['url']} | {r['seed']} | {r['status']} | {r['steps']} |" for r in runs]
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None, browser=None) -> int:
    parser = argparse.ArgumentParser(prog="simux", description=__doc__.split("\n")[0])
    sub = parser.add_subparsers(dest="command", required=True)
    run_p = sub.add_parser("run", help="audit the pages in .simux.yaml")
    run_p.add_argument("--config", type=Path, default=Path(CONFIG_FILE))
    run_p.add_argument("--out", type=Path, default=Path("findings.json"))
    run_p.add_argument("--logs", type=Path, help="run logs (default: a temporary folder)")
    run_p.add_argument("--summary", type=Path, help="also write a Markdown summary here")
    args = parser.parse_args(argv)

    config = load_config(args.config)
    logs = args.logs or Path(tempfile.mkdtemp(prefix="simux-"))
    findings, runs, changes = audit_pages(config, args.config.resolve().parent, logs, browser)
    failing = [f for f in findings if f.severity >= config.fail_on]
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps(
            {
                "persona": config.persona,
                "fail_on": config.fail_on,
                "failed": bool(failing),
                "runs": runs,
                "findings": changes,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    text = summary_markdown(findings, runs, config.fail_on)
    if args.summary:
        with open(args.summary, "a", encoding="utf-8") as f:
            f.write(text)
    print(text)
    print(f"Wrote {args.out}; logs in {logs}")
    if failing:
        return 1
    if runs and all(r["status"] in ("aborted_provider", "crashed") for r in runs):
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
