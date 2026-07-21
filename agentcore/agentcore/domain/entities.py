from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any, TypedDict


class TaskPlan(TypedDict):
    task: str
    tool: str
    tool_input: dict[str, Any]


class TaskResult(TypedDict):
    task: str
    tool: str
    result: Any
    success: bool


class AgentState(TypedDict):
    # Configuration (set once at start)
    run_id: str
    goal: str
    model: str
    max_iterations: int
    budget_usd: float
    allowed_tools: list[str]

    # Planning output
    plan: list[TaskPlan]

    # Execution state
    current_task_index: int
    results: list[TaskResult]
    retry_count: int
    iteration_count: int

    # Cost tracking
    cost_usd: float
    input_tokens: int
    output_tokens: int

    # Terminal
    final_answer: str | None
    error: str | None
    status: str  # running | completed | failed | killed


@dataclass(frozen=True)
class RunRecord:
    id: str
    goal: str
    model: str
    status: str
    iteration_count: int
    input_tokens: int
    output_tokens: int
    cost_usd: Decimal
    error: str | None
    started_at: datetime | None
