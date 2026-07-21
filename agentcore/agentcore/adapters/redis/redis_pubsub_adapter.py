import json
from collections.abc import AsyncGenerator
from typing import Any

from agentcore.adapters.redis.connection import get_redis_pool

_CHANNEL = "run:{run_id}"


class RedisPubSubAdapter:
    def __init__(self, redis_url: str) -> None:
        self._redis_url = redis_url

    async def publish(self, run_id: str, event: dict[str, Any]) -> None:
        try:
            r = await get_redis_pool(self._redis_url)
            await r.publish(_CHANNEL.format(run_id=run_id), str(event))
        except Exception:
            pass  # stream failure must not break the agent

    async def subscribe(self, run_id: str) -> AsyncGenerator[dict[str, Any], None]:
        r = await get_redis_pool(self._redis_url)
        pubsub = r.pubsub()
        try:
            await pubsub.subscribe(_CHANNEL.format(run_id=run_id))
            async for message in pubsub.listen():
                if message["type"] == "message":
                    try:
                        yield json.loads(message["data"].replace("'", '"'))
                    except Exception:
                        yield {"raw": str(message["data"])}
        finally:
            await pubsub.unsubscribe()
