import hmac

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader
from sqlalchemy.ext.asyncio import AsyncSession

from agentcore.adapters.db.sqlalchemy_run_repository import SqlAlchemyRunRepository
from agentcore.application.dto import AgentDefaults
from agentcore.application.services.agent_run_service import AgentRunService
from agentcore.config import settings
from agentcore.db.session import get_session

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=True)


def require_api_key(key: str = Security(api_key_header)) -> str:
    if not hmac.compare_digest(key, settings.agentcore_api_key):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")
    return key


def get_agent_defaults() -> AgentDefaults:
    return AgentDefaults(
        model=settings.openrouter_default_model,
        max_iterations=settings.default_max_iterations,
        max_tokens=settings.default_max_tokens,
        budget_usd=settings.default_budget_usd,
        tools=["web_search", "http_caller", "memory_read", "memory_write"],
    )


def get_agent_run_service(
    session: AsyncSession = Depends(get_session),  # noqa: B008
    defaults: AgentDefaults = Depends(get_agent_defaults),  # noqa: B008
) -> AgentRunService:
    return AgentRunService(SqlAlchemyRunRepository(session), defaults)
