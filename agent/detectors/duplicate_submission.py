"""`duplicate_submission` (B4): one submit gesture sends the same request twice.

Spec, P1 table: a double submit produces two submissions, counted from the
network log. Nielsen #5, WCAG 3.3.4 Error Prevention.

Counted within one step only: two identical requests (method, URL and body)
caused by the same action. A persona that submits again in a later step,
on purpose, is not this signal.
"""

from collections import Counter

from agent.contracts import Finding
from agent.detectors import RunLog, make_finding

SIGNAL = "duplicate_submission"


def duplicate_submission(run: RunLog) -> Finding | None:
    sent = Counter((s.step, s.method, s.url, s.body) for s in run.submissions)
    evidence = sorted({step for (step, *_), n in sent.items() if n >= 2})
    return make_finding(run, SIGNAL, evidence) if evidence else None
