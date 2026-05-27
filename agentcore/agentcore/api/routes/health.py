import redis.asyncio as aioredis
from fastapi import APIRouter
from sqlalchemy import text

from agentcore.config import settings
from agentcore.db.session import engine

router = APIRouter(tags=["health"])


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/ready")
async def ready() -> dict[str, str]:
    results: dict[str, str] = {}

    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        results["db"] = "ok"
    except Exception:
        results["db"] = "error"

    try:
        r = aioredis.from_url(settings.redis_url)
        await r.ping()
        await r.aclose()  # type: ignore[attr-defined]
        results["redis"] = "ok"
    except Exception:
        results["redis"] = "error"

    results["status"] = "ok" if all(v == "ok" for v in results.values()) else "error"
    return results
