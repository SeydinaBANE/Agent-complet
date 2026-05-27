from decimal import Decimal

import pytest

from agentcore.guardrails.budget import BudgetExceededError, check_budget, compute_cost
from agentcore.guardrails.iterations import MaxIterationsError, check_iterations
from agentcore.guardrails.scope import ScopeViolationError, check_url_scope


def test_compute_cost_zero_tokens() -> None:
    assert compute_cost(0, 0) == Decimal("0")


def test_compute_cost_positive() -> None:
    cost = compute_cost(1_000_000, 1_000_000)
    assert cost > 0


def test_budget_not_exceeded() -> None:
    check_budget(Decimal("0.05"), 0.10, "run-1")  # should not raise


def test_budget_exceeded() -> None:
    with pytest.raises(BudgetExceededError):
        check_budget(Decimal("0.15"), 0.10, "run-1")


def test_iterations_not_exceeded() -> None:
    check_iterations(5, 10, "run-1")  # should not raise


def test_iterations_exceeded() -> None:
    with pytest.raises(MaxIterationsError):
        check_iterations(10, 10, "run-1")


def test_scope_allows_public_url() -> None:
    check_url_scope("https://example.com/api", "run-1")  # should not raise


def test_scope_blocks_localhost() -> None:
    with pytest.raises(ScopeViolationError):
        check_url_scope("http://localhost:8080/secret", "run-1")


def test_scope_blocks_aws_metadata() -> None:
    with pytest.raises(ScopeViolationError):
        check_url_scope("http://169.254.169.254/latest/meta-data/", "run-1")
