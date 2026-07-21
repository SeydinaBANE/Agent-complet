from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from agentcore.adapters.redis.redis_pubsub_adapter import RedisPubSubAdapter


@pytest.mark.asyncio
async def test_publish_sends_event_on_run_channel() -> None:
    mock_redis = AsyncMock()

    with patch(
        "agentcore.adapters.redis.redis_pubsub_adapter.get_redis_pool",
        new_callable=AsyncMock,
        return_value=mock_redis,
    ):
        await RedisPubSubAdapter("redis://localhost:6379").publish("run-1", {"type": "started"})

    mock_redis.publish.assert_called_once()
    args = mock_redis.publish.call_args[0]
    assert args[0] == "run:run-1"


@pytest.mark.asyncio
async def test_publish_swallows_redis_errors() -> None:
    with patch(
        "agentcore.adapters.redis.redis_pubsub_adapter.get_redis_pool",
        new_callable=AsyncMock,
        side_effect=RuntimeError("connection refused"),
    ):
        await RedisPubSubAdapter("redis://localhost:6379").publish("run-1", {"type": "started"})


@pytest.mark.asyncio
async def test_subscribe_yields_parsed_events() -> None:
    mock_pubsub = AsyncMock()

    async def _messages() -> object:
        for msg in [
            {"type": "subscribe", "data": 1},
            {"type": "message", "data": '{"type": "tool_call"}'},
        ]:
            yield msg

    mock_pubsub.listen = MagicMock(return_value=_messages())
    mock_redis = AsyncMock()
    mock_redis.pubsub = MagicMock(return_value=mock_pubsub)

    with patch(
        "agentcore.adapters.redis.redis_pubsub_adapter.get_redis_pool",
        new_callable=AsyncMock,
        return_value=mock_redis,
    ):
        events = [
            event async for event in RedisPubSubAdapter("redis://localhost:6379").subscribe("run-1")
        ]

    assert events == [{"type": "tool_call"}]
    mock_pubsub.unsubscribe.assert_called_once()
