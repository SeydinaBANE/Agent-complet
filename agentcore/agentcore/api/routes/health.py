import redis.asyncio as aioredis
from fastapi import APIRouter
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from agentcore.config import settings

router = APIRouter(tags=["health"])


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/ready")
async def ready() -> dict[str, str]:
    results: dict[str, str] = {}

    try:
        engine = create_async_engine(settings.database_url)
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        await engine.dispose()
        results["db"] = "ok"
    except Exception:
        results["db"] = "error"

    try:
        r = aioredis.from_url(settings.redis_url)
        await r.ping()
        await r.aclose()
        results["redis"] = "ok"
    except Exception:
        results["redis"] = "error"

    all_ok = all(v == "ok" for v in results.values())
    results["status"] = "ok" if all_ok else "error"
    return results
