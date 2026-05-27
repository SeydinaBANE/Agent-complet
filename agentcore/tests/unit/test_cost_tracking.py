from decimal import Decimal

from agentcore.guardrails.budget import compute_cost


def test_cost_scales_with_tokens() -> None:
    cost_small = compute_cost(1000, 1000)
    cost_large = compute_cost(10_000, 10_000)
    assert cost_large > cost_small


def test_output_tokens_cost_more_than_input() -> None:
    cost_input = compute_cost(1_000_000, 0)
    cost_output = compute_cost(0, 1_000_000)
    assert cost_output > cost_input


def test_cost_precision() -> None:
    cost = compute_cost(100, 100)
    assert isinstance(cost, Decimal)
    assert cost >= Decimal("0")
