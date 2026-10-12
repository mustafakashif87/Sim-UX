# grounding

Maps a detector's signal to candidate criteria, quotes the corpus, and verifies the quote.

- `signal_map.yaml`: signal to candidate criteria; the single source of truth (team-reviewed).
- `corpus/wcag22.yaml`, `corpus/nielsen.yaml`: one entry per criterion, text copied verbatim from the official page with its URL. Nielsen holds short attributed excerpts only.
- `ground.py`: `SignalMap`, `Corpus`, `verify_quote`, `ground_finding`, `severity`, `start_confidence`.

Mid-eval scope is the stub (spec steps 1, 2, 5, 6): an exact-text lookup in place of vector retrieval, with the LLM's quote supplied by the caller. A citation is kept only when its criterion is a candidate and its quote is an exact substring of the corpus entry (whitespace runs collapsed, nothing else). Failing citations are dropped and the finding is returned ungrounded with confidence halved.

To add a criterion: copy its text from the W3C Understanding page (never from memory), add the entry to the corpus, list it in `signal_map.yaml`, and run `pytest tests/test_grounding.py`.

Owner: Person C. Spec: Grounding pipeline.
