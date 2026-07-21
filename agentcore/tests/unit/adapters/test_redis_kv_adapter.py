from unittest.mock import AsyncMock, patch

import pytest

from agentcore.adapters.redis.redis_kv_adapter import RedisKvAdapter


@pytest.mark.asyncio
async def test_write_then_read() -> None:
    mock_redis = AsyncMock()
    mock_redis.get.return_value = "hello"

    with patch(
        "agentcore.adapters.redis.redis_kv_adapter.get_redis_pool",
        new_callable=AsyncMock,
        return_value=mock_redis,
    ):
        value = await RedisKvAdapter("redis://localhost:6379").get("my_key")

    assert value == "hello"
    mock_redis.get.assert_called_once_with("agent:memory:my_key")


@pytest.mark.asyncio
async def test_read_missing_key() -> None:
    mock_redis = AsyncMock()
    mock_redis.get.return_value = None

    with patch(
        "agentcore.adapters.redis.redis_kv_adapter.get_redis_pool",
        new_callable=AsyncMock,
        return_value=mock_redis,
    ):
        value = await RedisKvAdapter("redis://localhost:6379").get("missing")

    assert value is None


@pytest.mark.asyncio
async def test_set_writes_with_ttl() -> None:
    mock_redis = AsyncMock()

    with patch(
        "agentcore.adapters.redis.redis_kv_adapter.get_redis_pool",
        new_callable=AsyncMock,
        return_value=mock_redis,
    ):
        await RedisKvAdapter("redis://localhost:6379").set("key", "value", ttl=3600)

    mock_redis.set.assert_called_once_with("agent:memory:key", "value", ex=3600)
