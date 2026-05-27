import structlog
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_fastapi_instrumentator import Instrumentator
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from agentcore.api.routes import agents, eval, health, tools
from agentcore.config import settings

log = structlog.get_logger()

limiter = Limiter(key_func=get_remote_address, default_limits=["60/minute"])

app = FastAPI(
    title="AgentCore",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

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
app.include_router(eval.router, prefix="/api/v1")


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    log.error("unhandled_error", path=request.url.path, error=str(exc))
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"error": "internal_error", "detail": "An unexpected error occurred"},
    )
