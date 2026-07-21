import hmac

from fastapi import Depends, HTTPException, Request, Security, status
from fastapi.security import APIKeyHeader
from sqlalchemy.ext.asyncio import AsyncSession

from agentcore.adapters.db.sqlalchemy_audit_adapter import SqlAlchemyAuditAdapter
from agentcore.adapters.db.sqlalchemy_run_repository import SqlAlchemyRunRepository
from agentcore.adapters.queue.arq_queue_adapter import ArqQueueAdapter
from agentcore.adapters.redis.redis_kv_adapter import RedisKvAdapter
from agentcore.adapters.redis.redis_pubsub_adapter import RedisPubSubAdapter
from agentcore.application.dto import AgentDefaults
from agentcore.application.services.agent_run_service import AgentRunService
from agentcore.application.services.run_stream_service import RunStreamService
from agentcore.config import settings
from agentcore.db.session import get_session
from agentcore.domain.services.audit_service import AuditService
from agentcore.ports.audit_port import AuditPort
from agentcore.ports.kv_store_port import KvStorePort
from agentcore.ports.pubsub_port import PubSubPort

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
    request: Request,
    session: AsyncSession = Depends(get_session),  # noqa: B008
    defaults: AgentDefaults = Depends(get_agent_defaults),  # noqa: B008
) -> AgentRunService:
    return AgentRunService(
        SqlAlchemyRunRepository(session),
        ArqQueueAdapter(request.app.state.arq),
        defaults,
    )


def get_kv_store() -> KvStorePort:
    return RedisKvAdapter(settings.redis_url)


def get_pubsub() -> PubSubPort:
    return RedisPubSubAdapter(settings.redis_url)


def get_run_stream_service(
    pubsub: PubSubPort = Depends(get_pubsub),  # noqa: B008
) -> RunStreamService:
    return RunStreamService(pubsub)


def get_audit_service(
    session: AsyncSession = Depends(get_session),  # noqa: B008
) -> AuditService:
    audit_port: AuditPort = SqlAlchemyAuditAdapter(session)
    return AuditService(audit_port)
