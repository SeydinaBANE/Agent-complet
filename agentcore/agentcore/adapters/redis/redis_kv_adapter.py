from agentcore.adapters.redis.connection import get_redis_pool

DEFAULT_TTL_SECONDS = 86400  # 24h
_KEY_PREFIX = "agent:memory:"


class RedisKvAdapter:
    def __init__(self, redis_url: str) -> None:
        self._redis_url = redis_url

    async def get(self, key: str) -> str | None:
        r = await get_redis_pool(self._redis_url)
        return await r.get(f"{_KEY_PREFIX}{key}")

    async def set(self, key: str, value: str, ttl: int = DEFAULT_TTL_SECONDS) -> None:
        r = await get_redis_pool(self._redis_url)
        await r.set(f"{_KEY_PREFIX}{key}", value, ex=ttl)
