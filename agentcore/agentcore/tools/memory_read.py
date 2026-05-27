import redis.asyncio as aioredis

from agentcore.config import settings


async def read_memory(key: str = "", run_id: str = "", **_kwargs: object) -> str | None:
    r = aioredis.from_url(settings.redis_url)
    try:
        value = await r.get(f"agent:memory:{key}")
        return value.decode() if value else None
    finally:
        await r.aclose()  # type: ignore[attr-defined]
