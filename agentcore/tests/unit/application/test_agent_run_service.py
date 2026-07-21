from decimal import Decimal
from typing import Any

import pytest

from agentcore.application.dto import AgentDefaults
from agentcore.application.services.agent_run_service import AgentRunService
from agentcore.domain.entities import RunRecord
from agentcore.domain.errors import RunNotFoundError


class _FakeRunRepository:
    def __init__(self) -> None:
        self.records: dict[str, RunRecord] = {}

    async def create(self, run_id: str, goal: str, model: str) -> None:
        self.records[run_id] = RunRecord(
            id=run_id,
            goal=goal,
            model=model,
            status="pending",
            iteration_count=0,
            input_tokens=0,
            output_tokens=0,
            cost_usd=Decimal("0"),
            error=None,
            started_at=None,
        )

    async def mark_running(self, run_id: str) -> None:
        raise NotImplementedError

    async def mark_finished(self, *args: object, **kwargs: object) -> None:
        raise NotImplementedError

    async def get_by_id(self, run_id: str) -> RunRecord | None:
        return self.records.get(run_id)

    async def list(self, cursor: str | None, limit: int) -> list[RunRecord]:
        return list(self.records.values())[:limit]


class _FakeQueue:
    def __init__(self) -> None:
        self.enqueued: list[dict[str, Any]] = []

    async def enqueue_agent_job(
        self,
        run_id: str,
        goal: str,
        model: str,
        max_iterations: int,
        budget_usd: float,
        max_tokens: int,
        allowed_tools: list[str],
    ) -> None:
        self.enqueued.append(
            {
                "run_id": run_id,
                "goal": goal,
                "model": model,
                "max_iterations": max_iterations,
                "budget_usd": budget_usd,
                "max_tokens": max_tokens,
                "allowed_tools": allowed_tools,
            }
        )


def _defaults() -> AgentDefaults:
    return AgentDefaults(
        model="openai/gpt-4o-mini",
        max_iterations=10,
        max_tokens=4000,
        budget_usd=0.10,
        tools=["web_search"],
    )


@pytest.mark.asyncio
async def test_start_run_uses_defaults_when_unset() -> None:
    queue = _FakeQueue()
    service = AgentRunService(_FakeRunRepository(), queue, _defaults())

    run_id = await service.start_run(
        goal="find the best Python LLM framework",
        model=None,
        max_iterations=None,
        max_tokens=None,
        budget_usd=None,
        tools=None,
    )

    assert queue.enqueued[0]["run_id"] == run_id
    assert queue.enqueued[0]["model"] == "openai/gpt-4o-mini"
    assert queue.enqueued[0]["max_iterations"] == 10
    assert queue.enqueued[0]["allowed_tools"] == ["web_search"]


@pytest.mark.asyncio
async def test_start_run_respects_explicit_overrides() -> None:
    queue = _FakeQueue()
    service = AgentRunService(_FakeRunRepository(), queue, _defaults())

    await service.start_run(
        goal="goal",
        model="openai/gpt-4o",
        max_iterations=5,
        max_tokens=1000,
        budget_usd=0.05,
        tools=["http_caller"],
    )

    assert queue.enqueued[0]["model"] == "openai/gpt-4o"
    assert queue.enqueued[0]["max_iterations"] == 5
    assert queue.enqueued[0]["allowed_tools"] == ["http_caller"]


@pytest.mark.asyncio
async def test_get_run_raises_when_missing() -> None:
    service = AgentRunService(_FakeRunRepository(), _FakeQueue(), _defaults())

    with pytest.raises(RunNotFoundError):
        await service.get_run("nonexistent")


@pytest.mark.asyncio
async def test_get_run_returns_record() -> None:
    repo = _FakeRunRepository()
    service = AgentRunService(repo, _FakeQueue(), _defaults())
    run_id = await service.start_run(
        goal="goal", model=None, max_iterations=None, max_tokens=None, budget_usd=None, tools=None
    )

    run = await service.get_run(run_id)

    assert run.id == run_id
    assert run.goal == "goal"
