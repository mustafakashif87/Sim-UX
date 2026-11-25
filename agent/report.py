"""Findings as change requests: what went wrong, what to change on the page,
and where (the element the persona was acting on at the first evidence step,
and the page path). Shared by the API and `simux run`."""

import json
import re
from functools import cache
from pathlib import Path

import yaml

from agent.contracts import Finding

FIXES_PATH = Path(__file__).resolve().parent.parent / "grounding" / "fixes.yaml"


@cache
def fixes() -> dict[str, dict[str, str]]:
    return yaml.safe_load(FIXES_PATH.read_text(encoding="utf-8"))


def _lines(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def element_for(tree: str, ref: str) -> str | None:
    """`button "Place order"` for `ref` in an aria snapshot tree, or None."""
    for line in tree.splitlines():
        if f"[ref={ref}]" in line:
            text = line.strip().removeprefix("- ")
            text = re.sub(r"\s*\[[^\]]*\]", "", text).rstrip(":").strip()
            return text or None
    return None


def where(log_dir: Path, step: int) -> dict:
    """The page path and element of one step, as far as the log tells."""
    record = next((s for s in _lines(log_dir / "steps.jsonl") if s["step"] == step), None)
    obs = next((o for o in _lines(log_dir / "observations.jsonl") if o["step"] == step), None)
    observation = (obs or {}).get("observation", {})
    action = (record or {}).get("executed_action") or (record or {}).get("intended_action") or {}
    ref = action.get("ref")
    element = element_for(observation.get("tree", ""), ref) if ref else None
    return {
        "path": observation.get("url_path"),
        "element": element,
        "thought": action.get("thought"),
    }


def explain(findings: list[Finding], log_dir: Path) -> list[dict]:
    """Each finding as JSON plus `problem`, `fix` and `where`, most severe first."""
    out = []
    for f in sorted(findings, key=lambda f: (-f.severity, -f.confidence)):
        text = fixes().get(f.signal, {})
        out.append(
            {
                **f.model_dump(mode="json"),
                "problem": text.get("problem"),
                "fix": text.get("fix"),
                "where": where(log_dir, f.evidence_steps[0]),
            }
        )
    return out
