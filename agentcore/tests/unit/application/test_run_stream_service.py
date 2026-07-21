from collections.abc import AsyncGenerator
from typing import Any

import pytest

from agentcore.application.services.run_stream_service import RunStreamService


class _FakePubSub:
    async def publish(self, run_id: str, event: dict[str, Any]) -> None:
        raise NotImplementedError

    async def subscribe(self, run_id: str) -> AsyncGenerator[dict[str, Any], None]:
        yield {"type": "subscribed", "run_id": run_id}
        yield {"type": "completed"}


@pytest.mark.asyncio
async def test_subscribe_delegates_to_pubsub_port() -> None:
    service = RunStreamService(_FakePubSub())

    events = [event async for event in service.subscribe("run-1")]

    assert events == [{"type": "subscribed", "run_id": "run-1"}, {"type": "completed"}]
