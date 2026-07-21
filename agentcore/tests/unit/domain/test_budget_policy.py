from decimal import Decimal

import pytest

from agentcore.domain.errors import BudgetExceededError
from agentcore.domain.services.budget_policy import check_budget, compute_cost


def test_compute_cost_zero_tokens() -> None:
    assert compute_cost(0, 0) == Decimal("0")


def test_compute_cost_positive() -> None:
    cost = compute_cost(1_000_000, 1_000_000)
    assert cost > 0


def test_compute_cost_scales_with_tokens() -> None:
    cost_small = compute_cost(1000, 1000)
    cost_large = compute_cost(10_000, 10_000)
    assert cost_large > cost_small


def test_compute_cost_output_tokens_cost_more_than_input() -> None:
    cost_input = compute_cost(1_000_000, 0)
    cost_output = compute_cost(0, 1_000_000)
    assert cost_output > cost_input


def test_budget_not_exceeded() -> None:
    check_budget(Decimal("0.05"), 0.10, "run-1")  # should not raise


def test_budget_exceeded() -> None:
    with pytest.raises(BudgetExceededError):
        check_budget(Decimal("0.15"), 0.10, "run-1")
