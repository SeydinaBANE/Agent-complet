from decimal import Decimal

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
    service = AgentRunService(_FakeRunRepository(), _defaults())

    plan = await service.start_run(
        goal="find the best Python LLM framework",
        model=None,
        max_iterations=None,
        max_tokens=None,
        budget_usd=None,
        tools=None,
    )

    assert plan.model == "openai/gpt-4o-mini"
    assert plan.max_iterations == 10
    assert plan.tools == ["web_search"]


@pytest.mark.asyncio
async def test_start_run_respects_explicit_overrides() -> None:
    service = AgentRunService(_FakeRunRepository(), _defaults())

    plan = await service.start_run(
        goal="goal",
        model="openai/gpt-4o",
        max_iterations=5,
        max_tokens=1000,
        budget_usd=0.05,
        tools=["http_caller"],
    )

    assert plan.model == "openai/gpt-4o"
    assert plan.max_iterations == 5
    assert plan.tools == ["http_caller"]


@pytest.mark.asyncio
async def test_get_run_raises_when_missing() -> None:
    service = AgentRunService(_FakeRunRepository(), _defaults())

    with pytest.raises(RunNotFoundError):
        await service.get_run("nonexistent")


@pytest.mark.asyncio
async def test_get_run_returns_record() -> None:
    repo = _FakeRunRepository()
    service = AgentRunService(repo, _defaults())
    plan = await service.start_run(
        goal="goal", model=None, max_iterations=None, max_tokens=None, budget_usd=None, tools=None
    )

    run = await service.get_run(plan.run_id)

    assert run.id == plan.run_id
    assert run.goal == "goal"
