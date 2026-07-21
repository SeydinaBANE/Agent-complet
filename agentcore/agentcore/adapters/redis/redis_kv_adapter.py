"""Redis key-value adapter — KvStorePort implementation.

Stores agent memory as key-value pairs in Redis with a configurable TTL.
Keys are prefixed with ``agent:memory:`` to avoid collisions with other
Redis usage (pub/sub channels, ARQ jobs, etc.).
"""

from agentcore.adapters.redis.connection import get_redis_pool

DEFAULT_TTL_SECONDS = 86400  # 24h
_KEY_PREFIX = "agent:memory:"


class RedisKvAdapter:
    """KvStorePort backed by Redis GET/SET with automatic key prefixing."""

    def __init__(self, redis_url: str) -> None:
        self._redis_url = redis_url

    async def get(self, key: str) -> str | None:
        """Retrieve a value by key.

        Args:
            key: Logical key (prefix is added automatically).

        Returns:
            The stored string value, or None if the key does not exist.
        """
        r = await get_redis_pool(self._redis_url)
        return await r.get(f"{_KEY_PREFIX}{key}")

    async def set(self, key: str, value: str, ttl: int = DEFAULT_TTL_SECONDS) -> None:
        """Store a value with a time-to-live.

        Args:
            key: Logical key (prefix is added automatically).
            value: String value to store.
            ttl: Time-to-live in seconds (default 24 hours).
        """
        r = await get_redis_pool(self._redis_url)
        await r.set(f"{_KEY_PREFIX}{key}", value, ex=ttl)
