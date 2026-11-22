"""`simux` config and summary: no browser."""

from pathlib import Path

import pytest
from pydantic import ValidationError

from agent.cli import Config, load_config, summary_markdown

FIXTURES = Path(__file__).parents[1] / "examples" / "action-fixture"


def test_fixture_configs_load():
    for name in ("order-a", "order-b"):
        config = load_config(FIXTURES / f"{name}.simux.yaml")
        assert config.persona == "error_prone" and config.fail_on == 2
        assert config.pages[0].url == f"{name}.html"


@pytest.mark.parametrize(
    "bad",
    [
        {"pages": []},
        {
            "pages": [{"url": "x.html", "task": "t", "goal": {"role": "heading", "name": "Done"}}],
            "fail_on": 5,
        },
        {
            "pages": [
                {"url": "x.html", "task": "t", "goal": {"role": "heading", "name": "D"}, "typo": 1}
            ]
        },
    ],
)
def test_bad_configs_are_rejected(bad):
    with pytest.raises(ValidationError):
        Config.model_validate(bad)


def test_summary_marks_failing_findings():
    from agent.contracts import Finding

    f = Finding(
        finding_id="r-duplicate_submission",
        persona="error_prone",
        page="order-a.html",
        signal="duplicate_submission",
        evidence_steps=[0],
        candidate_criteria=["Nielsen 5", "WCAG 3.3.4"],
        severity=2,
        confidence=0.9,
        baseline_reproduced=False,
    )
    runs = [{"url": "order-a.html", "seed": 1, "status": "succeeded", "steps": 1}]
    text = summary_markdown([f], runs, fail_on=2)
    assert "| order-a.html | `duplicate_submission` | 2 (fails) |" in text
    assert "No findings in 1 run(s)." in summary_markdown([], runs, fail_on=2)
