import uuid
from typing import Annotated

import structlog
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, status
from pydantic import BaseModel, Field

from agentcore.api.deps import require_api_key
from agentcore.config import settings

log = structlog.get_logger()
router = APIRouter(tags=["agents"])


class AgentRunRequest(BaseModel):
    goal: str = Field(..., min_length=1, max_length=2000)
    model: str = Field(default_factory=lambda: settings.openrouter_default_model)
    max_iterations: int = Field(default_factory=lambda: settings.default_max_iterations, ge=1, le=50)
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
async def start_run(body: AgentRunRequest) -> AgentRunResponse:
    run_id = str(uuid.uuid4())
    log.info("run_enqueued", run_id=run_id, goal=body.goal[:80], model=body.model)
    # TODO: enqueue ARQ job
    return AgentRunResponse(run_id=run_id, status="pending")


@router.get(
    "/agents/{run_id}",
    response_model=RunStatus,
    dependencies=[Depends(require_api_key)],
)
async def get_run(run_id: str) -> RunStatus:
    # TODO: fetch from DB
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Run not found")


@router.post(
    "/agents/{run_id}/stop",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_api_key)],
)
async def stop_run(run_id: str) -> None:
    log.info("run_stop_requested", run_id=run_id)
    # TODO: set cancelled flag in Redis


@router.get(
    "/agents",
    dependencies=[Depends(require_api_key)],
)
async def list_runs(cursor: str | None = None, limit: int = 20) -> dict:
    # TODO: cursor-based pagination from DB
    return {"data": [], "next_cursor": None}


@router.websocket("/agents/{run_id}/stream")
async def stream_run(websocket: WebSocket, run_id: str) -> None:
    await websocket.accept()
    try:
        log.info("ws_connected", run_id=run_id)
        # TODO: subscribe to Redis pub/sub channel for run_id
        await websocket.send_json({"type": "connected", "run_id": run_id})
        while True:
            # Heartbeat until real stream is implemented
            await websocket.receive_text()
    except WebSocketDisconnect:
        log.info("ws_disconnected", run_id=run_id)
