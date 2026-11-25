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


# Findings about the whole page, not the element the persona was acting on.
PAGE_WIDE = {
    "no_structure",
    "headings_not_descriptive",
    "key_info_buried",
    "cta_below_fold",
    "lost_location",
    "no_progress_indicator",
    "reflow_failure",
    "text_clipped",
    "help_unreachable",
    "help_inconsistent",
    "inconsistent_identification",
    "inconsistent_navigation",
    "excess_steps",
    "no_bulk_action",
}
# Findings about an element with no name: point at the first such element.
UNNAMED = {
    "unnamed_control": ("button", "link", "textbox", "checkbox", "radio", "combobox"),
    "button-name": ("button",),
    "image_only_info": ("img",),
    "image-alt": ("img",),
}


def unnamed_in(tree: str, roles: tuple[str, ...]) -> str | None:
    """`button (no name)` for the first node of these roles with no name."""
    for line in tree.splitlines():
        m = re.match(r"\s*- (\w+) \[", line)
        if m and m.group(1) in roles:
            return f"{m.group(1)} (no name)"
    return None


def where(log_dir: Path, step: int, signal: str = "") -> dict:
    """The page path and element of one step, as far as the log tells."""
    record = next((s for s in _lines(log_dir / "steps.jsonl") if s["step"] == step), None)
    obs = next((o for o in _lines(log_dir / "observations.jsonl") if o["step"] == step), None)
    observation = (obs or {}).get("observation", {})
    path = observation.get("url_path")
    if signal in PAGE_WIDE:
        return {"path": path, "element": None, "thought": None}
    if signal in UNNAMED:
        tree = (obs or {}).get("full_tree") or observation.get("tree", "")
        return {"path": path, "element": unnamed_in(tree, UNNAMED[signal]), "thought": None}
    action = (record or {}).get("executed_action") or (record or {}).get("intended_action") or {}
    ref = action.get("ref")
    element = element_for(observation.get("tree", ""), ref) if ref else None
    return {
        "path": path,
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
                "where": where(log_dir, f.evidence_steps[0], f.signal),
            }
        )
    return out
