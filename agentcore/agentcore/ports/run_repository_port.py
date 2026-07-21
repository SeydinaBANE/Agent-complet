from typing import Protocol

from agentcore.domain.entities import RunRecord


class RunRepositoryPort(Protocol):
    async def create(self, run_id: str, goal: str, model: str) -> None: ...

    async def mark_running(self, run_id: str) -> None: ...

    async def mark_finished(
        self,
        run_id: str,
        status: str,
        iteration_count: int,
        input_tokens: int,
        output_tokens: int,
        cost_usd: float,
        error: str | None,
    ) -> None: ...

    async def get_by_id(self, run_id: str) -> RunRecord | None: ...

    async def list(self, cursor: str | None, limit: int) -> list[RunRecord]: ...
