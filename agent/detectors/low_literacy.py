"""P3 Low-literacy or non-native reader: `label_unintelligible`,
`instruction_unintelligible`, `system_language` (spec, P3 table).

The logged observations are what P3 saw: the tree after `vocab_filter`, with
unknown words as [unknown]. In the baseline condition the filter is off, so
no [unknown] appears and none of these fire.

- `label_unintelligible` (B10, Nielsen #2, WCAG 3.3.2): the run did not
  succeed, and a control the persona saw has half or more of its name's words
  [unknown].
- `instruction_unintelligible` (B11, Nielsen #2, WCAG 3.1.5): a paragraph or
  text of MIN_INSTRUCTION_WORDS or more words has more than half of its
  content words (not "of", "the", "shall") [unknown].
- `system_language` (B12, Nielsen #2): an alert or error text contains an
  internal code (an identifier joined by underscores, or capitals with
  digits such as ERR422) instead of words. The spec lists it as
  model-judged; this deterministic rule was chosen on 22 Nov 2026.
"""

import re

from agent.contracts import Finding
from agent.detectors import RunLog, make_finding
from agent.detectors._tree import nodes
from agent.vocab import UNKNOWN, unknown_share

_CONTROL_ROLES = {"button", "link", "textbox", "checkbox", "radio", "combobox", "menuitem"}
_TEXT_ROLES = {"paragraph", "text", "note", "status"}
MIN_INSTRUCTION_WORDS = 8
_CODE = re.compile(
    r"(?:\[unknown\]|[A-Za-z0-9]+)(?:_(?:\[unknown\]|[A-Za-z0-9]+))+|\b[A-Z]{2,}[-_]?\d{2,}\b"
)


def label_unintelligible(run: RunLog) -> Finding | None:
    if run.meta.get("status") == "succeeded":
        return None
    for i, obs in enumerate(run.observations):
        for n in nodes(obs):
            if n.role in _CONTROL_ROLES and n.name and UNKNOWN in n.name:
                if unknown_share(n.name) >= 0.5:
                    return make_finding(run, "label_unintelligible", [i])
    return None


def instruction_unintelligible(run: RunLog) -> Finding | None:
    for i, obs in enumerate(run.observations):
        for n in nodes(obs):
            text = n.text if n.role in _TEXT_ROLES else None
            if not text or len(re.findall(r"\[unknown\]|[A-Za-z]+", text)) < MIN_INSTRUCTION_WORDS:
                continue
            if unknown_share(text, content_only=True) > 0.5:
                return make_finding(run, "instruction_unintelligible", [i])
    return None


def system_language(run: RunLog) -> Finding | None:
    for i, obs in enumerate(run.observations):
        for n in nodes(obs):
            if n.role == "alert" and _CODE.search(n.text or n.name or ""):
                return make_finding(run, "system_language", [i])
    return None
