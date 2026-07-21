from typing import Any, cast

from agentcore.domain.entities import AgentState
from agentcore.domain.services.graph_transition_policy import should_continue


def _base_state(**overrides: Any) -> AgentState:
    state: dict[str, Any] = {
        "run_id": "run-1",
        "goal": "goal",
        "model": "openai/gpt-4o-mini",
        "max_iterations": 10,
        "budget_usd": 0.10,
        "allowed_tools": [],
        "plan": [],
        "current_task_index": 0,
        "results": [],
        "retry_count": 0,
        "iteration_count": 0,
        "cost_usd": 0.0,
        "input_tokens": 0,
        "output_tokens": 0,
        "final_answer": None,
        "error": None,
        "status": "running",
    }
    state.update(overrides)
    return cast(AgentState, state)


def test_should_continue_stops_on_error() -> None:
    assert should_continue(_base_state(error="boom")) == "stop"


def test_should_continue_stops_on_completed_status() -> None:
    assert should_continue(_base_state(status="completed")) == "stop"


def test_should_continue_continues_when_tasks_remain() -> None:
    from agentcore.domain.entities import TaskPlan

    plan = [TaskPlan(task="t", tool="web_search", tool_input={})]
    assert should_continue(_base_state(plan=plan, current_task_index=0)) == "continue"


def test_should_continue_stops_when_plan_exhausted() -> None:
    assert should_continue(_base_state(plan=[], current_task_index=0)) == "stop"
