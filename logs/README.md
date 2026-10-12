# logs

Evaluation run logs. Raw logs are append-only evidence: record corrections in
a notes column, never by editing a log.

Owner: Person A. Spec: Evaluation protocol.

| Path | Contents |
| --- | --- |
| `axe/<date>/` | axe-core 4.10.2 scan of every `test-app/` page (`.github/scripts/axe-scan.mjs`): one JSON per page plus `summary.json` |

## axe-core results, 2026-10-12

| Bug | Buggy page | Clean page | axe-core |
| --- | --- | --- | --- |
| SB-01 | `image-alt` | none | detected |
| SB-02 | `button-name` | none | detected |
| SB-03 | `label` | none | detected |
| SB-04 | none | none | **missed** (focus trap is runtime behaviour) |
| SB-05 | none | none | **missed** (a `<div>` with a click handler is valid markup) |

No violations on any clean page, `index.html` or `success.html`. This is the
axe-core column of the comparison table (spec: Comparison systems), and the
evidence that the keyboard sweep is needed for 2.1.1 and 2.1.2.

## axe-core results, 2026-10-12, run 2 (with B1 to B6)

`axe/2026-10-12-run2/`: the same scan after the P1 pages were added. SB-01 to
SB-05 results are unchanged. axe-core reports **no violation on any B1 to B6
page, buggy or clean**: all six are behavioural (what happens after a submit,
a double press or a step change), so a static scan cannot see them. That
column of the comparison table is therefore 0/6 for B1 to B6, which is the
spec's case for task-based personas. No page has an unplanned violation.
