from typing import Protocol


class QueuePort(Protocol):
    async def enqueue_agent_job(
        self,
        run_id: str,
        goal: str,
        model: str,
        max_iterations: int,
        budget_usd: float,
        max_tokens: int,
        allowed_tools: list[str],
    ) -> None: ...
