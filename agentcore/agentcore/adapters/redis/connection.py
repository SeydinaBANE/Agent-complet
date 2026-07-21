from __future__ import annotations

import redis.asyncio as aioredis

_pool: aioredis.Redis[str] | None = None


async def get_redis_pool(redis_url: str) -> aioredis.Redis[str]:
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
    global _pool
    if _pool is not None:
        await _pool.aclose()  # type: ignore[attr-defined]
        _pool = None
