from typing import Any, cast
from unittest.mock import AsyncMock, patch

import pytest

from agentcore.agents.state import AgentState


def _base_state(**overrides: Any) -> AgentState:
    state: dict[str, Any] = {
        "run_id": "run-1",
        "goal": "find the best Python LLM framework",
        "model": "openai/gpt-4o-mini",
        "max_iterations": 10,
        "budget_usd": 0.10,
        "allowed_tools": ["web_search", "memory_read"],
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


@pytest.mark.asyncio
async def test_planner_node_creates_plan() -> None:
    from agentcore.agents.graph import _planner_node

    plan_data = [
        {"task": "search frameworks", "tool": "web_search", "tool_input": {"query": "Python LLM"}}
    ]

    with (
        patch("agentcore.agents.graph.chat_json", AsyncMock(return_value=(plan_data, 10, 20))),
        patch("agentcore.agents.graph._publish", AsyncMock()),
    ):
        result = await _planner_node(_base_state())

    assert len(result["plan"]) == 1
    assert result["plan"][0]["tool"] == "web_search"
    assert result["input_tokens"] == 10
    assert result["output_tokens"] == 20
    assert result["iteration_count"] == 1


@pytest.mark.asyncio
async def test_planner_node_handles_non_list_response() -> None:
    from agentcore.agents.graph import _planner_node

    with (
        patch(
            "agentcore.agents.graph.chat_json", AsyncMock(return_value=({"bad": "response"}, 5, 5))
        ),
        patch("agentcore.agents.graph._publish", AsyncMock()),
    ):
        result = await _planner_node(_base_state())

    # Falls back to single task
    assert len(result["plan"]) == 1


@pytest.mark.asyncio
async def test_executor_node_runs_tool() -> None:
    from agentcore.agents.graph import _executor_node
    from agentcore.agents.state import TaskPlan

    plan = [TaskPlan(task="search", tool="web_search", tool_input={"query": "LLM"})]
    state = _base_state(plan=plan, current_task_index=0)

    mock_result = [{"title": "LangChain", "url": "https://example.com", "snippet": "..."}]

    with (
        patch("agentcore.agents.graph.execute_tool", AsyncMock(return_value=mock_result)),
        patch("agentcore.agents.graph._publish", AsyncMock()),
    ):
        result = await _executor_node(state)

    assert result["current_task_index"] == 1
    assert len(result["results"]) == 1
    assert result["results"][0]["success"] is True


@pytest.mark.asyncio
async def test_executor_node_handles_tool_failure() -> None:
    from agentcore.agents.graph import _executor_node
    from agentcore.agents.state import TaskPlan

    plan = [TaskPlan(task="search", tool="web_search", tool_input={"query": "test"})]
    state = _base_state(plan=plan, current_task_index=0)

    with (
        patch(
            "agentcore.agents.graph.execute_tool",
            AsyncMock(side_effect=RuntimeError("network error")),
        ),
        patch("agentcore.agents.graph._publish", AsyncMock()),
    ):
        result = await _executor_node(state)

    assert result["results"][0]["success"] is False
    assert result["retry_count"] == 1


@pytest.mark.asyncio
async def test_executor_node_skips_when_all_done() -> None:
    from agentcore.agents.graph import _executor_node

    state = _base_state(plan=[], current_task_index=0)
    result = await _executor_node(state)
    assert result == {}


@pytest.mark.asyncio
async def test_validator_node_synthesizes_answer() -> None:
    from agentcore.agents.graph import _validator_node
    from agentcore.agents.state import TaskResult

    results = [TaskResult(task="search", tool="web_search", result={"data": "found"}, success=True)]
    state = _base_state(plan=[], current_task_index=0, results=results)

    with (
        patch("agentcore.agents.graph.chat", AsyncMock(return_value=("LangChain is best", 15, 10))),
        patch("agentcore.agents.graph._publish", AsyncMock()),
    ):
        result = await _validator_node(state)

    assert result["final_answer"] == "LangChain is best"
    assert result["status"] == "completed"


@pytest.mark.asyncio
async def test_validator_node_skips_when_tasks_remain() -> None:
    from agentcore.agents.graph import _validator_node
    from agentcore.agents.state import TaskPlan

    plan = [TaskPlan(task="t", tool="web_search", tool_input={})]
    state = _base_state(plan=plan, current_task_index=0)
    result = await _validator_node(state)
    assert result == {}


def test_build_graph_returns_compiled() -> None:
    from agentcore.agents.graph import build_graph

    g = build_graph()
    assert g is not None
