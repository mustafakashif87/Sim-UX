"""The grounding stub (spec: Grounding pipeline, steps 1, 2, 5 and 6).

1. A detector emits a signal and its evidence steps (see agent/detectors).
2. `SignalMap` lists the candidate criteria for that signal.
5. `verify_quote` and `ground_finding` keep a citation only when its criterion is
   a candidate and its quote is an exact substring of the corpus entry. Anything
   else is dropped and the finding is marked ungrounded with lower confidence; it
   is still reported, never hidden.
6. `severity` is rule-based on Nielsen's 0 to 4 scale.

Step 3 (vector retrieval) and the open pass come later. Until then the corpus is
an exact-text lookup table: one entry per criterion, found by its ID. The LLM
(step 4) is not called here; it will supply the `quotes` argument.
"""

from dataclasses import dataclass, field
from pathlib import Path

import yaml

from agent.contracts import Citation, Finding

HERE = Path(__file__).parent
SIGNAL_MAP_PATH = HERE / "signal_map.yaml"
CORPUS_PATHS = (HERE / "corpus" / "wcag22.yaml", HERE / "corpus" / "nielsen.yaml")

# Spec: confidence starts at 0.9 for deterministic signals and 0.6 for
# model-judged ones, then is multiplied by the reproduction rate across runs.
START_CONFIDENCE = {"deterministic": 0.9, "model_judged": 0.6}

# The spec says an ungrounded finding gets "lower confidence" without a number.
# Halving is our choice; change it here and in the report together.
UNGROUNDED_FACTOR = 0.5


def normalise(text: str) -> str:
    """Collapse runs of whitespace. The only change allowed before comparing."""
    return " ".join(text.split())


@dataclass(frozen=True)
class CorpusEntry:
    id: str
    source: str  # "WCAG" or "Nielsen", the Citation.source values
    title: str
    url: str
    text: str
    key_quote: str


class Corpus:
    def __init__(self, entries: list[CorpusEntry]):
        self._by_id = {e.id: e for e in entries}
        if len(self._by_id) != len(entries):
            raise ValueError("duplicate corpus entry id")

    def __contains__(self, criterion_id: str) -> bool:
        return criterion_id in self._by_id

    def __len__(self) -> int:
        return len(self._by_id)

    def get(self, criterion_id: str) -> CorpusEntry:
        return self._by_id[criterion_id]

    def ids(self) -> list[str]:
        return list(self._by_id)

    @classmethod
    def load(cls, paths=CORPUS_PATHS) -> "Corpus":
        entries = []
        for path in paths:
            for raw in yaml.safe_load(Path(path).read_text(encoding="utf-8")):
                entries.append(
                    CorpusEntry(
                        id=raw["id"],
                        source=raw["source"],
                        title=raw["title"],
                        url=raw["url"],
                        text=normalise(raw["text"]),
                        key_quote=normalise(raw["key_quote"]),
                    )
                )
        return cls(entries)


@dataclass(frozen=True)
class SignalEntry:
    source: str
    type: str
    criteria: list[str]


class SignalMap:
    def __init__(self, signals: dict[str, SignalEntry]):
        self._signals = signals

    def __contains__(self, signal: str) -> bool:
        return signal in self._signals

    def signals(self) -> list[str]:
        return list(self._signals)

    def entry(self, signal: str) -> SignalEntry:
        return self._signals[signal]

    def candidates(self, signal: str) -> list[str]:
        """Candidate criterion IDs for a signal, in the map's order."""
        return list(self._signals[signal].criteria)

    @classmethod
    def load(cls, path=SIGNAL_MAP_PATH) -> "SignalMap":
        raw = yaml.safe_load(Path(path).read_text(encoding="utf-8"))["signals"]
        return cls(
            {k: SignalEntry(v["source"], v["type"], list(v["criteria"])) for k, v in raw.items()}
        )

    def check_against(self, corpus: Corpus) -> list[str]:
        """Criteria the map lists that the corpus lacks (empty when consistent)."""
        return sorted({c for s in self._signals.values() for c in s.criteria if c not in corpus})


def default_corpus() -> Corpus:
    return Corpus.load()


def default_signal_map() -> SignalMap:
    return SignalMap.load()


def verify_quote(quote: str, entry: CorpusEntry) -> bool:
    """True only when the quote is an exact substring of the entry's text.

    Case, punctuation and wording must match; only whitespace runs are collapsed.
    A paraphrase fails (spec: Unit tests).
    """
    q = normalise(quote)
    return bool(q) and q in entry.text


def start_confidence(signal_type: str, reproduction_rate: float = 1.0) -> float:
    """0.9 or 0.6 by signal type, times the k/5 reproduction rate."""
    return START_CONFIDENCE[signal_type] * reproduction_rate


def severity(
    *,
    task_completed: bool,
    data_loss: bool = False,
    steps: int = 0,
    shortest_steps: int = 0,
    cosmetic: bool = False,
) -> int:
    """Nielsen's scale as the spec states it: 4 task blocked; 3 task completed
    with data loss or more than twice the shortest path; 2 recoverable friction;
    1 cosmetic."""
    if not task_completed:
        return 4
    if data_loss or (shortest_steps > 0 and steps > 2 * shortest_steps):
        return 3
    return 1 if cosmetic else 2


@dataclass(frozen=True)
class GroundingReport:
    finding: Finding
    grounded: bool
    dropped: list[tuple[str, str]] = field(default_factory=list)  # (criterion_id, reason)


def ground_finding(
    finding: Finding,
    corpus: Corpus,
    quotes: dict[str, str],
    *,
    ungrounded_factor: float = UNGROUNDED_FACTOR,
) -> GroundingReport:
    """Attach the citations that pass verification; mark the rest ungrounded.

    `quotes` maps a criterion ID to the quote written for it. A citation is kept
    when the ID is in the finding's candidate set, the corpus has the entry, and
    the quote is an exact substring of that entry. If none survive, the finding
    keeps no citations and its confidence is multiplied by `ungrounded_factor`.
    """
    kept: list[Citation] = []
    dropped: list[tuple[str, str]] = []
    for criterion_id, quote in quotes.items():
        if criterion_id not in finding.candidate_criteria:
            dropped.append((criterion_id, "not a candidate for this signal"))
        elif criterion_id not in corpus:
            dropped.append((criterion_id, "not in the corpus"))
        else:
            entry = corpus.get(criterion_id)
            if verify_quote(quote, entry):
                kept.append(Citation(source=entry.source, criterion_id=criterion_id, quote=quote))
            else:
                dropped.append((criterion_id, "quote is not in the corpus text"))
    grounded = bool(kept)
    update = {"citations": kept}
    if not grounded:
        update["confidence"] = finding.confidence * ungrounded_factor
    return GroundingReport(Finding(**{**finding.model_dump(), **update}), grounded, dropped)


def key_quotes(signal_map: SignalMap, corpus: Corpus, signal: str) -> dict[str, str]:
    """Stand-in for the LLM (step 4): each candidate's verbatim `key_quote`."""
    return {c: corpus.get(c).key_quote for c in signal_map.candidates(signal) if c in corpus}
