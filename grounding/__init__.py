"""Grounding: map a signal to candidate criteria, quote the corpus, verify the quote.

Spec: Grounding pipeline. Mid-eval scope is the stub: steps 1, 2, 5 and 6, with an
exact-text lookup table (the corpus) in place of vector retrieval.
"""

from grounding.ground import (
    Corpus,
    CorpusEntry,
    GroundingReport,
    SignalMap,
    default_corpus,
    default_signal_map,
    ground_finding,
    key_quotes,
    severity,
    start_confidence,
    verify_quote,
)

__all__ = [
    "Corpus",
    "CorpusEntry",
    "GroundingReport",
    "SignalMap",
    "default_corpus",
    "default_signal_map",
    "ground_finding",
    "key_quotes",
    "severity",
    "start_confidence",
    "verify_quote",
]
