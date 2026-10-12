# axe-core results per page

Summary of `2026-10-12-run2/` (axe-core 4.10.2 via `.github/scripts/axe-scan.mjs`,
all 24 pages in `test-app/`). Generated from `2026-10-12-run2/summary.json`;
the raw per-page JSON beside it is the evidence. This is the **axe-core column
of the comparison table** (spec: Comparison systems). CI uploads a fresh scan
as the `axe-results` artifact on every pull request.

| Page | Seeded bug | WCAG 2.2 | axe-core violations | Result |
| --- | --- | --- | --- | --- |
| `signup-a.html` | B1 buggy | 3.3.7 Redundant Entry | none | missed |
| `signup-b.html` | B1 clean | 3.3.7 Redundant Entry | none | correct: clean |
| `subscribe-a.html` | B2 buggy | 3.3.1 Error Identification | none | missed |
| `subscribe-b.html` | B2 clean | 3.3.1 Error Identification | none | correct: clean |
| `callback-a.html` | B3 buggy | 3.3.3 Error Suggestion | none | missed |
| `callback-b.html` | B3 clean | 3.3.3 Error Suggestion | none | correct: clean |
| `order-a.html` | B4 buggy | 3.3.4 Error Prevention | none | missed |
| `order-b.html` | B4 clean | 3.3.4 Error Prevention | none | correct: clean |
| `account-a.html` | B5 buggy | 3.3.4 Error Prevention | none | missed |
| `account-b.html` | B5 clean | 3.3.4 Error Prevention | none | correct: clean |
| `checkout-a.html` | B6 buggy | 3.3.7 Redundant Entry | none | missed |
| `checkout-b.html` | B6 clean | 3.3.7 Redundant Entry | none | correct: clean |
| `promo-a.html` | SB-01 buggy | 1.1.1 Non-text Content | `image-alt` (critical, 1 node) | detected |
| `promo-b.html` | SB-01 clean | 1.1.1 Non-text Content | none | correct: clean |
| `search-a.html` | SB-02 buggy | 4.1.2 Name, Role, Value | `button-name` (critical, 1 node) | detected |
| `search-b.html` | SB-02 clean | 4.1.2 Name, Role, Value | none | correct: clean |
| `contact-a.html` | SB-03 buggy | 1.3.1 Info and Relationships | `label` (critical, 1 node) | detected |
| `contact-b.html` | SB-03 clean | 1.3.1 Info and Relationships | none | correct: clean |
| `basket-a.html` | SB-04 buggy | 2.1.2 No Keyboard Trap | none | missed |
| `basket-b.html` | SB-04 clean | 2.1.2 No Keyboard Trap | none | correct: clean |
| `booking-a.html` | SB-05 buggy | 2.1.1 Keyboard | none | missed |
| `booking-b.html` | SB-05 clean | 2.1.1 Keyboard | none | correct: clean |
| `index.html` | not a test target | n/a | none | correct: clean |
| `success.html` | not a test target | n/a | none | correct: clean |

## Totals

| | Count |
| --- | --- |
| Seeded bugs detected (buggy pages) | **3 / 11**: SB-01, SB-02, SB-03 |
| Missed: behavioural P1 bugs (B1 to B6) | 6 / 6 |
| Missed: keyboard bugs (SB-04, SB-05) | 2 / 2 |
| Violations on clean pages (false positives) | **0 / 11** |
| Unplanned violations on any page | 0 |

Every axe-core hit is a real seeded bug (precision 3/3), but it sees only the
static ones. All six P1 bugs and both keyboard bugs need someone to *use* the
page (submit, double-press, change step, Tab through), which a static scan
never does. B1 to B6 are covered by the P1 persona's detectors, and SB-04 and
SB-05 by the planned keyboard sweep.
