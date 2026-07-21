"""Queue port — interface for enqueuing background agent jobs.

The queue decouples API request handling from agent execution,
allowing runs to be processed asynchronously by a worker.
"""

from typing import Protocol


class QueuePort(Protocol):
    """Protocol for job queue implementations (ARQ, BullMQ, etc.)."""

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
        """Enqueue an agent run for background execution.

        Args:
            run_id: Unique identifier for the run.
            goal: User-provided objective for the agent.
            model: LLM model identifier (e.g. openai/gpt-4o-mini).
            max_iterations: Maximum number of executor loops.
            budget_usd: Maximum spend in USD before the run is killed.
            max_tokens: Maximum tokens per LLM call.
            allowed_tools: Whitelist of tool names the agent may use.
        """
