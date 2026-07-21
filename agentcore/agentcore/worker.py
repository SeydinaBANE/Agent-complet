"""ARQ background worker — composition root for agent execution.

This module assembles all adapters (LLM, tools, DB, Redis, pub/sub)
into a single ``run_agent_job`` function that ARQ invokes asynchronously.
It also defines ``WorkerSettings`` for the ARQ worker process.
"""

from typing import Any

import structlog
from arq.connections import RedisSettings

from agentcore.adapters.db.sqlalchemy_run_repository import SqlAlchemyRunRepository
from agentcore.adapters.http.httpx_client_adapter import HttpxClientAdapter
from agentcore.adapters.langgraph.graph_factory import build_graph
from agentcore.adapters.llm.openrouter_llm_adapter import OpenRouterLlmAdapter
from agentcore.adapters.redis.redis_kv_adapter import RedisKvAdapter
from agentcore.adapters.redis.redis_pubsub_adapter import RedisPubSubAdapter
from agentcore.adapters.tools.ddgs_web_search_adapter import DdgsWebSearchAdapter
from agentcore.adapters.tools.http_caller_tool_adapter import HttpCallerToolAdapter
from agentcore.adapters.tools.memory_read_tool_adapter import MemoryReadToolAdapter
from agentcore.adapters.tools.memory_write_tool_adapter import MemoryWriteToolAdapter
from agentcore.adapters.tools.tool_registry import StaticToolRegistry
from agentcore.adapters.tools.web_search_tool_adapter import WebSearchToolAdapter
from agentcore.application.services.agent_orchestrator import AgentOrchestrator
from agentcore.application.services.tool_execution_service import ToolExecutionService
from agentcore.config import Settings, settings
from agentcore.db.session import SessionLocal
from agentcore.domain.entities import AgentState
from agentcore.ports.tool_port import ToolPort

MAX_DB_RETRIES = 3
RETRY_DELAY_SECONDS = 1


def _build_tool_registry(cfg: Settings) -> StaticToolRegistry:
    """Assemble all tool adapters into a static registry.

    Args:
        cfg: Application settings containing Redis URL.

    Returns:
        A ToolRegistryPort with all four tools registered.
    """
    kv = RedisKvAdapter(cfg.redis_url)
    tools: dict[str, ToolPort] = {
        "web_search": WebSearchToolAdapter(DdgsWebSearchAdapter()),
        "http_caller": HttpCallerToolAdapter(HttpxClientAdapter()),
        "memory_read": MemoryReadToolAdapter(kv),
        "memory_write": MemoryWriteToolAdapter(kv),
    }
    return StaticToolRegistry(tools)


log = structlog.get_logger()

_CANCEL_KEY = "run:cancel:{run_id}"


async def _mark_running_with_retry(run_id: str) -> None:
    """Mark a run as running with automatic retry on transient DB errors.

    Args:
        run_id: The run to update.

    Raises:
        Exception: Re-raised after MAX_DB_RETRIES failed attempts.
    """
    for attempt in range(MAX_DB_RETRIES):
        try:
            async with SessionLocal() as session:
                await SqlAlchemyRunRepository(session).mark_running(run_id)
                return
        except Exception:
            if attempt == MAX_DB_RETRIES - 1:
                raise
            log.warning("db_retry", operation="mark_running", attempt=attempt + 1)


async def _mark_finished_with_retry(run_id: str, **kwargs: Any) -> None:
    """Mark a run as finished with automatic retry on transient DB errors.

    Args:
        run_id: The run to update.
        **kwargs: Fields to set (status, iteration_count, tokens, cost, error).
    """
    for attempt in range(MAX_DB_RETRIES):
        try:
            async with SessionLocal() as session:
                await SqlAlchemyRunRepository(session).mark_finished(run_id, **kwargs)
                return
        except Exception:
            if attempt == MAX_DB_RETRIES - 1:
                raise
            log.warning("db_retry", operation="mark_finished", attempt=attempt + 1)


async def run_agent_job(
    ctx: dict[str, Any],
    run_id: str,
    goal: str,
    model: str,
    max_iterations: int,
    budget_usd: float,
    max_tokens: int,
    allowed_tools: list[str],
) -> dict[str, Any]:
    """Execute a full agent run (planner → executor → validator loop).

    This is the ARQ job function invoked by the worker process.

    Args:
        ctx: ARQ job context (unused, required by ARQ signature).
        run_id: Unique identifier for this run.
        goal: User-provided objective.
        model: LLM model to use.
        max_iterations: Maximum executor loops.
        budget_usd: Cost ceiling in USD.
        max_tokens: Max tokens per LLM call.
        allowed_tools: Whitelist of tool names.

    Returns:
        Dict with ``run_id`` and final ``status``.
    """
    log.info("job_started", run_id=run_id)

    await _mark_running_with_retry(run_id)

    llm = OpenRouterLlmAdapter(
        api_key=settings.openrouter_api_key, base_url=settings.openrouter_base_url
    )
    tools = ToolExecutionService(_build_tool_registry(settings))
    pubsub = RedisPubSubAdapter(settings.redis_url)
    orchestrator = AgentOrchestrator(llm=llm, tools=tools, pubsub=pubsub)
    graph = build_graph(orchestrator)
    initial_state = AgentState(
        run_id=run_id,
        goal=goal,
        model=model,
        max_iterations=max_iterations,
        budget_usd=budget_usd,
        allowed_tools=allowed_tools,
        plan=[],
        current_task_index=0,
        results=[],
        retry_count=0,
        iteration_count=0,
        cost_usd=0.0,
        input_tokens=0,
        output_tokens=0,
        final_answer=None,
        error=None,
        status="running",
    )

    try:
        final_state: AgentState = await graph.ainvoke(initial_state)
    except Exception as exc:
        log.error("job_failed", run_id=run_id, error=str(exc))
        final_state = {**initial_state, "status": "failed", "error": str(exc)}

    await _mark_finished_with_retry(
        run_id,
        status=final_state.get("status", "failed"),
        iteration_count=final_state.get("iteration_count", 0),
        input_tokens=final_state.get("input_tokens", 0),
        output_tokens=final_state.get("output_tokens", 0),
        cost_usd=final_state.get("cost_usd", 0),
        error=final_state.get("error"),
    )

    log.info("job_finished", run_id=run_id, status=final_state.get("status"))
    return {"run_id": run_id, "status": final_state.get("status")}


def _redis_settings() -> RedisSettings:
    """Build ARQ Redis connection settings from the application config."""
    url = settings.redis_url
    return RedisSettings.from_dsn(url)


class WorkerSettings:
    """ARQ worker configuration.

    Attributes:
        functions: List of job functions this worker can execute.
        redis_settings: Redis connection for the ARQ job queue.
        max_jobs: Maximum concurrent jobs per worker process.
        job_timeout: Maximum seconds before a job is killed.
        max_tries: Number of attempts before a job is marked as failed.
        retry_delay: Seconds to wait between retry attempts.
    """

    functions = [run_agent_job]
    redis_settings = _redis_settings()
    max_jobs = 10
    job_timeout = 300
    max_tries = 3
    retry_delay = 10
