"""Redis connection pool — shared async connection management.

Provides a singleton Redis connection pool reused across all adapters
(KvStore, PubSub, Cancellation). Connections are created lazily on
first use and closed gracefully on application shutdown.
"""

from __future__ import annotations

import redis.asyncio as aioredis

_pool: aioredis.Redis[str] | None = None


async def get_redis_pool(redis_url: str) -> aioredis.Redis[str]:
    """Return the shared Redis connection pool, creating it if needed.

    Args:
        redis_url: Redis connection URL (e.g. redis://localhost:6379).

    Returns:
        A connected async Redis client with decode_responses=True.
    """
    global _pool
    if _pool is None:
        _pool = aioredis.from_url(
            redis_url,
            decode_responses=True,
            max_connections=20,
            retry_on_timeout=True,
        )
    return _pool


async def close_redis_pool() -> None:
    """Close the shared Redis connection pool.

    Should be called during application shutdown to release connections.
    """
    global _pool
    if _pool is not None:
        await _pool.aclose()  # type: ignore[attr-defined]
        _pool = None
