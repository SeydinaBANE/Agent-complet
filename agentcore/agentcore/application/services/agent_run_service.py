import uuid

from agentcore.application.dto import AgentDefaults, AgentRunPlan
from agentcore.domain.entities import RunRecord
from agentcore.domain.errors import RunNotFoundError
from agentcore.ports.run_repository_port import RunRepositoryPort


class AgentRunService:
    def __init__(self, runs: RunRepositoryPort, defaults: AgentDefaults) -> None:
        self._runs = runs
        self._defaults = defaults

    async def start_run(
        self,
        goal: str,
        model: str | None,
        max_iterations: int | None,
        max_tokens: int | None,
        budget_usd: float | None,
        tools: list[str] | None,
    ) -> AgentRunPlan:
        run_id = str(uuid.uuid4())
        resolved_model = model or self._defaults.model
        await self._runs.create(run_id, goal, resolved_model)

        return AgentRunPlan(
            run_id=run_id,
            goal=goal,
            model=resolved_model,
            max_iterations=max_iterations or self._defaults.max_iterations,
            max_tokens=max_tokens or self._defaults.max_tokens,
            budget_usd=budget_usd or self._defaults.budget_usd,
            tools=tools or self._defaults.tools,
        )

    async def get_run(self, run_id: str) -> RunRecord:
        run = await self._runs.get_by_id(run_id)
        if run is None:
            raise RunNotFoundError(f"Run {run_id} not found")
        return run

    async def list_runs(self, cursor: str | None, limit: int) -> tuple[list[RunRecord], str | None]:
        runs = await self._runs.list(cursor, limit)
        next_cursor = runs[-1].id if len(runs) == limit else None
        return runs, next_cursor
