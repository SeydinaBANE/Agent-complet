import redis.asyncio as aioredis

from agentcore.config import settings

DEFAULT_TTL_SECONDS = 86400  # 24h


async def write_memory(key: str, value: str, ttl: int = DEFAULT_TTL_SECONDS, run_id: str = "") -> bool:
    r = aioredis.from_url(settings.redis_url)
    try:
        await r.set(f"agent:memory:{key}", value, ex=ttl)
        return True
    finally:
        await r.aclose()
