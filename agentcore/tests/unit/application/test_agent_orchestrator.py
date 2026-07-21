from typing import Any, cast
from unittest.mock import AsyncMock, patch

import pytest

from agentcore.application.services.agent_orchestrator import AgentOrchestrator
from agentcore.domain.entities import AgentState, TaskPlan, TaskResult


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


def _orchestrator(llm: AsyncMock) -> AgentOrchestrator:
    return AgentOrchestrator(llm=llm)


@pytest.mark.asyncio
async def test_plan_creates_plan_from_llm_response() -> None:
    llm = AsyncMock()
    plan_data = [
        {"task": "search frameworks", "tool": "web_search", "tool_input": {"query": "Python LLM"}}
    ]
    llm.chat_json = AsyncMock(return_value=(plan_data, 10, 20))

    with patch("agentcore.application.services.agent_orchestrator._publish", AsyncMock()):
        result = await _orchestrator(llm).plan(_base_state())

    assert len(result["plan"]) == 1
    assert result["plan"][0]["tool"] == "web_search"
    assert result["input_tokens"] == 10
    assert result["output_tokens"] == 20
    assert result["iteration_count"] == 1


@pytest.mark.asyncio
async def test_plan_handles_non_list_llm_response() -> None:
    llm = AsyncMock()
    llm.chat_json = AsyncMock(return_value=({"bad": "response"}, 5, 5))

    with patch("agentcore.application.services.agent_orchestrator._publish", AsyncMock()):
        result = await _orchestrator(llm).plan(_base_state())

    assert len(result["plan"]) == 1


@pytest.mark.asyncio
async def test_execute_task_runs_tool() -> None:
    plan = [TaskPlan(task="search", tool="web_search", tool_input={"query": "LLM"})]
    state = _base_state(plan=plan, current_task_index=0)
    mock_result = [{"title": "LangChain", "url": "https://example.com", "snippet": "..."}]

    with (
        patch(
            "agentcore.application.services.agent_orchestrator.execute_tool",
            AsyncMock(return_value=mock_result),
        ),
        patch("agentcore.application.services.agent_orchestrator._publish", AsyncMock()),
    ):
        result = await _orchestrator(AsyncMock()).execute_task(state)

    assert result["current_task_index"] == 1
    assert len(result["results"]) == 1
    assert result["results"][0]["success"] is True


@pytest.mark.asyncio
async def test_execute_task_handles_tool_failure() -> None:
    plan = [TaskPlan(task="search", tool="web_search", tool_input={"query": "test"})]
    state = _base_state(plan=plan, current_task_index=0)

    with (
        patch(
            "agentcore.application.services.agent_orchestrator.execute_tool",
            AsyncMock(side_effect=RuntimeError("network error")),
        ),
        patch("agentcore.application.services.agent_orchestrator._publish", AsyncMock()),
    ):
        result = await _orchestrator(AsyncMock()).execute_task(state)

    assert result["results"][0]["success"] is False
    assert result["retry_count"] == 1


@pytest.mark.asyncio
async def test_execute_task_skips_when_all_done() -> None:
    state = _base_state(plan=[], current_task_index=0)
    result = await _orchestrator(AsyncMock()).execute_task(state)
    assert result == {}


@pytest.mark.asyncio
async def test_finalize_synthesizes_answer() -> None:
    llm = AsyncMock()
    llm.chat = AsyncMock(return_value=("LangChain is best", 15, 10))
    results = [TaskResult(task="search", tool="web_search", result={"data": "found"}, success=True)]
    state = _base_state(plan=[], current_task_index=0, results=results)

    with patch("agentcore.application.services.agent_orchestrator._publish", AsyncMock()):
        result = await _orchestrator(llm).finalize(state)

    assert result["final_answer"] == "LangChain is best"
    assert result["status"] == "completed"


@pytest.mark.asyncio
async def test_finalize_skips_when_tasks_remain() -> None:
    plan = [TaskPlan(task="t", tool="web_search", tool_input={})]
    state = _base_state(plan=plan, current_task_index=0)
    result = await _orchestrator(AsyncMock()).finalize(state)
    assert result == {}
