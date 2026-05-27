import uuid

import structlog
from fastapi import APIRouter, Depends, status
from pydantic import BaseModel

from agentcore.api.deps import require_api_key

log = structlog.get_logger()
router = APIRouter(tags=["eval"])


class EvalRunRequest(BaseModel):
    target_model: str = "openai/gpt-4o-mini"
    categories: list[str] = ["prompt_injection", "jailbreak", "reliability"]
    max_cases_per_category: int = 5


class EvalRunResponse(BaseModel):
    eval_id: str
    status: str


@router.post(
    "/eval/run",
    response_model=EvalRunResponse,
    status_code=status.HTTP_202_ACCEPTED,
    dependencies=[Depends(require_api_key)],
)
async def start_eval(body: EvalRunRequest) -> EvalRunResponse:
    eval_id = str(uuid.uuid4())
    log.info("eval_enqueued", eval_id=eval_id, categories=body.categories)
    # TODO: enqueue eval ARQ job
    return EvalRunResponse(eval_id=eval_id, status="pending")
