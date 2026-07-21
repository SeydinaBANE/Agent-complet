import redis.asyncio as aioredis

DEFAULT_TTL_SECONDS = 86400  # 24h
_KEY_PREFIX = "agent:memory:"


class RedisKvAdapter:
    def __init__(self, redis_url: str) -> None:
        self._redis_url = redis_url

    async def get(self, key: str) -> str | None:
        r = aioredis.from_url(self._redis_url)
        try:
            value = await r.get(f"{_KEY_PREFIX}{key}")
            return value.decode() if value else None
        finally:
            await r.aclose()  # type: ignore[attr-defined]

    async def set(self, key: str, value: str, ttl: int = DEFAULT_TTL_SECONDS) -> None:
        r = aioredis.from_url(self._redis_url)
        try:
            await r.set(f"{_KEY_PREFIX}{key}", value, ex=ttl)
        finally:
            await r.aclose()  # type: ignore[attr-defined]
