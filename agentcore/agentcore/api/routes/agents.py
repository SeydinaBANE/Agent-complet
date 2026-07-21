from typing import Any

import structlog
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    WebSocket,
    WebSocketDisconnect,
    status,
)
from pydantic import BaseModel, Field

from agentcore.api.deps import (
    get_agent_run_service,
    get_kv_store,
    get_run_stream_service,
    require_api_key,
)
from agentcore.application.services.agent_run_service import AgentRunService
from agentcore.application.services.run_stream_service import RunStreamService
from agentcore.domain.errors import RunNotFoundError
from agentcore.ports.kv_store_port import KvStorePort

log = structlog.get_logger()
router = APIRouter(tags=["agents"])

_CANCEL_KEY = "run:cancel:{run_id}"


class AgentRunRequest(BaseModel):
    goal: str = Field(..., min_length=1, max_length=2000)
    model: str | None = None
    max_iterations: int | None = Field(default=None, ge=1, le=50)
    max_tokens: int | None = Field(default=None, ge=100, le=32000)
    budget_usd: float | None = Field(default=None, gt=0, le=10.0)
    tools: list[str] | None = None


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
    service: AgentRunService = Depends(get_agent_run_service),  # noqa: B008
) -> AgentRunResponse:
    run_id = await service.start_run(
        goal=body.goal,
        model=body.model,
        max_iterations=body.max_iterations,
        max_tokens=body.max_tokens,
        budget_usd=body.budget_usd,
        tools=body.tools,
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
    service: AgentRunService = Depends(get_agent_run_service),  # noqa: B008
) -> RunStatus:
    try:
        run = await service.get_run(run_id)
    except RunNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return RunStatus(
        run_id=run.id,
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
async def stop_run(
    run_id: str,
    kv: KvStorePort = Depends(get_kv_store),  # noqa: B008
) -> None:
    await kv.set(_CANCEL_KEY.format(run_id=run_id), "1", ttl=600)
    log.info("run_stop_requested", run_id=run_id)


@router.get(
    "/agents",
    dependencies=[Depends(require_api_key)],
)
async def list_runs(
    cursor: str | None = None,
    limit: int = 20,
    service: AgentRunService = Depends(get_agent_run_service),  # noqa: B008
) -> dict[str, Any]:
    runs, next_cursor = await service.list_runs(cursor, limit)

    data = [
        {
            "run_id": r.id,
            "status": r.status,
            "goal": r.goal[:100],
            "model": r.model,
            "cost_usd": float(r.cost_usd),
            "started_at": r.started_at.isoformat() if r.started_at else None,
        }
        for r in runs
    ]
    return {"data": data, "next_cursor": next_cursor}


@router.websocket("/agents/{run_id}/stream")
async def stream_run(
    websocket: WebSocket,
    run_id: str,
    stream_service: RunStreamService = Depends(get_run_stream_service),  # noqa: B008
) -> None:
    await websocket.accept()
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
