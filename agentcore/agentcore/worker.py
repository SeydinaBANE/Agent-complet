import uuid
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

import structlog
from arq.connections import RedisSettings
from sqlalchemy import update

from agentcore.adapters.http.httpx_client_adapter import HttpxClientAdapter
from agentcore.adapters.langgraph.graph_factory import build_graph
from agentcore.adapters.llm.openrouter_llm_adapter import OpenRouterLlmAdapter
from agentcore.adapters.redis.redis_kv_adapter import RedisKvAdapter
from agentcore.adapters.tools.ddgs_web_search_adapter import DdgsWebSearchAdapter
from agentcore.adapters.tools.http_caller_tool_adapter import HttpCallerToolAdapter
from agentcore.adapters.tools.memory_read_tool_adapter import MemoryReadToolAdapter
from agentcore.adapters.tools.memory_write_tool_adapter import MemoryWriteToolAdapter
from agentcore.adapters.tools.tool_registry import StaticToolRegistry
from agentcore.adapters.tools.web_search_tool_adapter import WebSearchToolAdapter
from agentcore.application.services.agent_orchestrator import AgentOrchestrator
from agentcore.application.services.tool_execution_service import ToolExecutionService
from agentcore.config import Settings, settings
from agentcore.db.models import Run
from agentcore.db.session import SessionLocal
from agentcore.domain.entities import AgentState
from agentcore.ports.tool_port import ToolPort


def _build_tool_registry(cfg: Settings) -> StaticToolRegistry:
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
    log.info("job_started", run_id=run_id)

    async with SessionLocal() as session:
        await session.execute(
            update(Run)
            .where(Run.id == uuid.UUID(run_id))
            .values(status="running", started_at=datetime.now(UTC))
        )
        await session.commit()

    llm = OpenRouterLlmAdapter(
        api_key=settings.openrouter_api_key, base_url=settings.openrouter_base_url
    )
    tools = ToolExecutionService(_build_tool_registry(settings))
    orchestrator = AgentOrchestrator(llm=llm, tools=tools)
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

    async with SessionLocal() as session:
        await session.execute(
            update(Run)
            .where(Run.id == uuid.UUID(run_id))
            .values(
                status=final_state.get("status", "failed"),
                finished_at=datetime.now(UTC),
                iteration_count=final_state.get("iteration_count", 0),
                input_tokens=final_state.get("input_tokens", 0),
                output_tokens=final_state.get("output_tokens", 0),
                cost_usd=Decimal(str(final_state.get("cost_usd", 0))),
                error=final_state.get("error"),
            )
        )
        await session.commit()

    log.info("job_finished", run_id=run_id, status=final_state.get("status"))
    return {"run_id": run_id, "status": final_state.get("status")}


def _redis_settings() -> RedisSettings:
    url = settings.redis_url
    return RedisSettings.from_dsn(url)


class WorkerSettings:
    functions = [run_agent_job]
    redis_settings = _redis_settings()
    max_jobs = 10
    job_timeout = 300
