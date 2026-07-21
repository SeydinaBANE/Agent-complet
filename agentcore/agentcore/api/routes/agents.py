import uuid
from typing import Any

import redis.asyncio as aioredis
import structlog
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request,
    WebSocket,
    WebSocketDisconnect,
    status,
)
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from agentcore.adapters.redis.redis_pubsub_adapter import RedisPubSubAdapter
from agentcore.api.deps import require_api_key
from agentcore.application.services.run_stream_service import RunStreamService
from agentcore.config import settings
from agentcore.db.models import Run
from agentcore.db.session import get_session

log = structlog.get_logger()
router = APIRouter(tags=["agents"])

_CANCEL_KEY = "run:cancel:{run_id}"


class AgentRunRequest(BaseModel):
    goal: str = Field(..., min_length=1, max_length=2000)
    model: str = Field(default_factory=lambda: settings.openrouter_default_model)
    max_iterations: int = Field(
        default_factory=lambda: settings.default_max_iterations, ge=1, le=50
    )
    max_tokens: int = Field(default_factory=lambda: settings.default_max_tokens, ge=100, le=32000)
    budget_usd: float = Field(default_factory=lambda: settings.default_budget_usd, gt=0, le=10.0)
    tools: list[str] = Field(default=["web_search", "http_caller", "memory_read", "memory_write"])


class AgentRunResponse(BaseModel):
    run_id: str
    status: str


class RunStatus(BaseModel):
    run_id: str
    status: str
    goal: str
    model: str
    iteration_count: int
    input_tokens: int
    output_tokens: int
    cost_usd: float
    error: str | None


@router.post(
    "/agents/run",
    response_model=AgentRunResponse,
    status_code=status.HTTP_202_ACCEPTED,
    dependencies=[Depends(require_api_key)],
)
async def start_run(
    body: AgentRunRequest,
    request: Request,
    session: AsyncSession = Depends(get_session),  # noqa: B008
) -> AgentRunResponse:
    run_id = str(uuid.uuid4())

    # Persist run as pending
    run = Run(
        id=uuid.UUID(run_id),
        goal=body.goal,
        model=body.model,
        status="pending",
    )
    session.add(run)
    await session.commit()

    # Enqueue ARQ job
    await request.app.state.arq.enqueue_job(
        "run_agent_job",
        run_id=run_id,
        goal=body.goal,
        model=body.model,
        max_iterations=body.max_iterations,
        budget_usd=body.budget_usd,
        max_tokens=body.max_tokens,
        allowed_tools=body.tools,
    )

    log.info("run_enqueued", run_id=run_id, goal=body.goal[:80])
    return AgentRunResponse(run_id=run_id, status="pending")


@router.get(
    "/agents/{run_id}",
    response_model=RunStatus,
    dependencies=[Depends(require_api_key)],
)
async def get_run(
    run_id: str,
    session: AsyncSession = Depends(get_session),  # noqa: B008
) -> RunStatus:
    result = await session.execute(select(Run).where(Run.id == uuid.UUID(run_id)))
    run = result.scalar_one_or_none()
    if not run:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Run not found")

    return RunStatus(
        run_id=str(run.id),
        status=run.status,
        goal=run.goal,
        model=run.model,
        iteration_count=run.iteration_count,
        input_tokens=run.input_tokens,
        output_tokens=run.output_tokens,
        cost_usd=float(run.cost_usd),
        error=run.error,
    )


@router.post(
    "/agents/{run_id}/stop",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_api_key)],
)
async def stop_run(run_id: str) -> None:
    r = aioredis.from_url(settings.redis_url)
    try:
        await r.set(_CANCEL_KEY.format(run_id=run_id), "1", ex=600)
    finally:
        await r.aclose()  # type: ignore[attr-defined]
    log.info("run_stop_requested", run_id=run_id)


@router.get(
    "/agents",
    dependencies=[Depends(require_api_key)],
)
async def list_runs(
    cursor: str | None = None,
    limit: int = 20,
    session: AsyncSession = Depends(get_session),  # noqa: B008
) -> dict[str, Any]:
    query = select(Run).order_by(Run.id).limit(min(limit, 100))
    if cursor:
        import contextlib

        with contextlib.suppress(ValueError):
            query = query.where(Run.id > uuid.UUID(cursor))

    result = await session.execute(query)
    runs = result.scalars().all()

    data = [
        {
            "run_id": str(r.id),
            "status": r.status,
            "goal": r.goal[:100],
            "model": r.model,
            "cost_usd": float(r.cost_usd),
            "started_at": r.started_at.isoformat() if r.started_at else None,
        }
        for r in runs
    ]
    next_cursor = str(runs[-1].id) if len(runs) == limit else None
    return {"data": data, "next_cursor": next_cursor}


@router.websocket("/agents/{run_id}/stream")
async def stream_run(websocket: WebSocket, run_id: str) -> None:
    await websocket.accept()
    stream_service = RunStreamService(RedisPubSubAdapter(settings.redis_url))
    log.info("ws_subscribed", run_id=run_id)
    await websocket.send_json({"type": "subscribed", "run_id": run_id})

    events = stream_service.subscribe(run_id)
    try:
        async for payload in events:
            await websocket.send_json(payload)
            if payload.get("type") in ("completed", "failed"):
                break
    except WebSocketDisconnect:
        log.info("ws_disconnected", run_id=run_id)
    finally:
        await events.aclose()
