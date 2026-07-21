from arq.connections import ArqRedis


class ArqQueueAdapter:
    def __init__(self, pool: ArqRedis) -> None:
        self._pool = pool

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
        await self._pool.enqueue_job(
            "run_agent_job",
            run_id=run_id,
            goal=goal,
            model=model,
            max_iterations=max_iterations,
            budget_usd=budget_usd,
            max_tokens=max_tokens,
            allowed_tools=allowed_tools,
        )
