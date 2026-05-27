import pytest

from agentcore.eval.adversarial import ADVERSARIAL_CASES
from agentcore.eval.suite import run_eval_suite


def test_adversarial_cases_not_empty() -> None:
    assert len(ADVERSARIAL_CASES) > 0


def test_adversarial_cases_have_required_fields() -> None:
    for case in ADVERSARIAL_CASES:
        assert "category" in case
        assert "input" in case
        assert "should_refuse" in case


@pytest.mark.asyncio
async def test_eval_suite_returns_report() -> None:
    report = await run_eval_suite(
        eval_id="test-eval",
        target_model="openai/gpt-4o-mini",
        categories=["prompt_injection", "reliability"],
    )
    assert "eval_id" in report
    assert report["eval_id"] == "test-eval"
    assert "score" in report
    assert "total" in report
    assert report["total"] > 0


@pytest.mark.asyncio
async def test_eval_suite_filters_by_category() -> None:
    all_report = await run_eval_suite(
        "e1", "gpt-4o-mini", ["prompt_injection", "jailbreak", "reliability"]
    )
    single_report = await run_eval_suite("e2", "gpt-4o-mini", ["reliability"])
    assert single_report["total"] < all_report["total"]


@pytest.mark.asyncio
async def test_eval_suite_empty_category() -> None:
    report = await run_eval_suite("e1", "gpt-4o-mini", ["nonexistent_category"])
    assert report["total"] == 0
