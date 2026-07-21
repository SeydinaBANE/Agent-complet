from unittest.mock import AsyncMock

import pytest

from agentcore.adapters.tools.memory_read_tool_adapter import MemoryReadToolAdapter
from agentcore.adapters.tools.memory_write_tool_adapter import MemoryWriteToolAdapter


@pytest.mark.asyncio
async def test_memory_read_dispatches_to_kv_port() -> None:
    kv = AsyncMock()
    kv.get = AsyncMock(return_value="cached")

    result = await MemoryReadToolAdapter(kv).run({"key": "k"}, run_id="r1")

    kv.get.assert_called_once_with("k")
    assert result == "cached"


@pytest.mark.asyncio
async def test_memory_write_dispatches_to_kv_port() -> None:
    kv = AsyncMock()
    kv.set = AsyncMock()

    result = await MemoryWriteToolAdapter(kv).run(
        {"key": "k", "value": "v", "ttl": 3600}, run_id="r1"
    )

    kv.set.assert_called_once_with("k", "v", 3600)
    assert result is True
