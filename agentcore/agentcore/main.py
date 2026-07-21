from contextlib import asynccontextmanager
from typing import Any

import structlog
from arq import create_pool
from arq.connections import RedisSettings
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_fastapi_instrumentator import Instrumentator
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from agentcore.adapters.http.httpx_client_adapter import close_client as close_http_client
from agentcore.adapters.redis.connection import close_redis_pool
from agentcore.api.routes import agents, health, tools
from agentcore.config import settings
from agentcore.db.session import engine

log = structlog.get_logger()

limiter = Limiter(key_func=get_remote_address, default_limits=["60/minute"])


@asynccontextmanager
async def lifespan(app: FastAPI) -> Any:
    # Startup
    arq_pool = await create_pool(RedisSettings.from_dsn(settings.redis_url))
    app.state.arq = arq_pool
    log.info("startup_complete")
    yield
    # Shutdown
    await arq_pool.aclose()  # type: ignore[attr-defined]
    await close_redis_pool()
    await close_http_client()
    await engine.dispose()
    log.info("shutdown_complete")


app = FastAPI(
    title="AgentCore",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)  # type: ignore[arg-type]

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.flowrunner_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*", "X-API-Key"],
)

Instrumentator().instrument(app).expose(app)

app.include_router(health.router)
app.include_router(agents.router, prefix="/api/v1")
app.include_router(tools.router, prefix="/api/v1")


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    log.error("unhandled_error", path=request.url.path, error=str(exc))
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"error": "internal_error", "detail": "An unexpected error occurred"},
    )
