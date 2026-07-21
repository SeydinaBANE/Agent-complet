from decimal import Decimal

import structlog

from agentcore.domain.errors import BudgetExceededError

log = structlog.get_logger()

# OpenRouter pricing is per 1M tokens — approximate defaults
DEFAULT_PRICE_PER_1M_INPUT = Decimal("0.15")
DEFAULT_PRICE_PER_1M_OUTPUT = Decimal("0.60")


def compute_cost(input_tokens: int, output_tokens: int) -> Decimal:
    return (
        Decimal(input_tokens) / 1_000_000 * DEFAULT_PRICE_PER_1M_INPUT
        + Decimal(output_tokens) / 1_000_000 * DEFAULT_PRICE_PER_1M_OUTPUT
    )


def check_budget(current_cost: Decimal, budget_usd: float, run_id: str) -> None:
    if current_cost >= Decimal(str(budget_usd)):
        log.warning("budget_exceeded", run_id=run_id, cost=float(current_cost), budget=budget_usd)
        raise BudgetExceededError(
            f"Run {run_id} exceeded budget ${budget_usd:.4f} (spent ${float(current_cost):.4f})"
        )
