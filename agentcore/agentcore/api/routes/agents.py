"""Agent routes — FastAPI endpoints for agent run management.

Provides REST endpoints for creating runs, querying status, stopping
runs (via Redis kill-switch), listing runs with cursor pagination,
and WebSocket streaming of real-time events.
"""

import asyncio
import hmac
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
from agentcore.config import settings
from agentcore.domain.errors import RunNotFoundError
from agentcore.ports.kv_store_port import KvStorePort

WS_TIMEOUT_SECONDS = 1800  # 30 minutes

log = structlog.get_logger()
router = APIRouter(tags=["agents"])

_CANCEL_KEY = "run:cancel:{run_id}"


class AgentRunRequest(BaseModel):
    """Request body for POST /agents/run."""

    goal: str = Field(..., min_length=1, max_length=2000)
    model: str | None = None
    max_iterations: int | None = Field(default=None, ge=1, le=50)
    max_tokens: int | None = Field(default=None, ge=100, le=32000)
    budget_usd: float | None = Field(default=None, gt=0, le=10.0)
    tools: list[str] | None = None


class AgentRunResponse(BaseModel):
    """Response for POST /agents/run."""

    run_id: str
    status: str


class RunStatus(BaseModel):
    """Detailed status of a single agent run."""

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
    """Enqueue a new agent run for background execution.

    Returns 202 Accepted with the run_id. Use GET /agents/{run_id}
    or WS /agents/{run_id}/stream to monitor progress.
    """
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
    """Retrieve current status and metrics for a specific run."""
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
    """Request cancellation of a running agent via Redis kill-switch.

    Writes a cancellation key to Redis with a 10-minute TTL.
    The worker checks this key at the start of each iteration.
    """
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
    """List agent runs with cursor-based pagination.

    Args:
        cursor: Opaque cursor from a previous response's ``next_cursor``.
        limit: Number of results to return (1-100, default 20).

    Returns:
        Dict with ``data`` (list of run summaries) and ``next_cursor``.
    """
    runs, next_cursor = await service.list_runs(cursor, max(1, min(limit, 100)))

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


async def _verify_ws_auth(websocket: WebSocket) -> None:
    """Authenticate a WebSocket connection via token or X-API-Key header.

    Closes the socket with code 4401 if authentication fails.

    Args:
        websocket: The incoming WebSocket connection.

    Raises:
        WebSocketDisconnect: If credentials are missing or invalid.
    """
    token = websocket.query_params.get("token") or websocket.headers.get("x-api-key")
    if not token or not hmac.compare_digest(str(token), settings.agentcore_api_key):
        await websocket.close(code=4401, reason="Unauthorized")
        raise WebSocketDisconnect(code=4401)


@router.websocket("/agents/{run_id}/stream")
async def stream_run(
    websocket: WebSocket,
    run_id: str,
    stream_service: RunStreamService = Depends(get_run_stream_service),  # noqa: B008
) -> None:
    """Stream real-time events for a run over WebSocket.

    Events include tool calls, status changes, and the final result.
    The connection auto-closes after 30 minutes or when the run completes.

    Client authentication: pass ``?token=<key>`` as query param or
    ``X-API-Key`` header.
    """
    await websocket.accept()
    await _verify_ws_auth(websocket)

    log.info("ws_subscribed", run_id=run_id)
    await websocket.send_json({"type": "subscribed", "run_id": run_id})

    events = stream_service.subscribe(run_id)
    try:
        async with asyncio.timeout(WS_TIMEOUT_SECONDS):
            async for payload in events:
                await websocket.send_json(payload)
                if payload.get("type") in ("completed", "failed"):
                    break
    except TimeoutError:
        log.info("ws_timeout", run_id=run_id)
        await websocket.send_json({"type": "error", "detail": "Stream timed out"})
    except WebSocketDisconnect:
        log.debug("ws_disconnected", run_id=run_id)
    finally:
        await events.aclose()
