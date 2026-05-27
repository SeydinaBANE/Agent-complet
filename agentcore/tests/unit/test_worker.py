from unittest.mock import AsyncMock, patch

import pytest


@pytest.mark.asyncio
async def test_run_agent_job_success() -> None:
    from agentcore.worker import run_agent_job

    final_state = {
        "status": "completed",
        "final_answer": "LangChain wins",
        "iteration_count": 3,
        "input_tokens": 100,
        "output_tokens": 50,
        "cost_usd": 0.002,
        "error": None,
    }

    mock_graph = AsyncMock()
    mock_graph.ainvoke = AsyncMock(return_value=final_state)

    mock_session = AsyncMock()
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=False)
    mock_session.execute = AsyncMock()
    mock_session.commit = AsyncMock()

    with (
        patch("agentcore.worker.build_graph", return_value=mock_graph),
        patch("agentcore.worker.SessionLocal", return_value=mock_session),
    ):
        result = await run_agent_job(
            ctx={},
            run_id="00000000-0000-0000-0000-000000000001",
            goal="find best LLM framework",
            model="openai/gpt-4o-mini",
            max_iterations=10,
            budget_usd=0.10,
            max_tokens=2000,
            allowed_tools=["web_search"],
        )

    assert result["status"] == "completed"
    assert result["run_id"] == "00000000-0000-0000-0000-000000000001"


@pytest.mark.asyncio
async def test_run_agent_job_handles_graph_exception() -> None:
    from agentcore.worker import run_agent_job

    mock_graph = AsyncMock()
    mock_graph.ainvoke = AsyncMock(side_effect=RuntimeError("graph crashed"))

    mock_session = AsyncMock()
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=False)
    mock_session.execute = AsyncMock()
    mock_session.commit = AsyncMock()

    with (
        patch("agentcore.worker.build_graph", return_value=mock_graph),
        patch("agentcore.worker.SessionLocal", return_value=mock_session),
    ):
        result = await run_agent_job(
            ctx={},
            run_id="00000000-0000-0000-0000-000000000002",
            goal="test goal",
            model="openai/gpt-4o-mini",
            max_iterations=5,
            budget_usd=0.05,
            max_tokens=1000,
            allowed_tools=[],
        )

    assert result["status"] == "failed"
