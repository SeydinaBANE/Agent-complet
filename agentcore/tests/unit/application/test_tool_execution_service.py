from typing import Any
from unittest.mock import AsyncMock

import pytest

from agentcore.application.services.tool_execution_service import ToolExecutionService
from agentcore.domain.errors import ToolNotFoundError
from agentcore.ports.tool_port import ToolPort


class _FakeRegistry:
    def __init__(self, tools: dict[str, ToolPort]) -> None:
        self._tools = tools

    def get(self, name: str) -> ToolPort:
        if name not in self._tools:
            raise ToolNotFoundError(f"Unknown tool: {name}")
        return self._tools[name]

    def list_tools(self) -> list[str]:
        return list(self._tools.keys())


class _FakeTool:
    name = "memory_read"

    async def run(self, tool_input: dict[str, Any], run_id: str) -> Any:
        return "cached"


@pytest.mark.asyncio
async def test_execute_dispatches_to_registered_tool() -> None:
    registry = _FakeRegistry({"memory_read": _FakeTool()})

    result = await ToolExecutionService(registry).execute("memory_read", {"key": "k"}, run_id="r1")

    assert result == "cached"


@pytest.mark.asyncio
async def test_execute_unknown_tool_raises() -> None:
    registry = _FakeRegistry({})

    with pytest.raises(ToolNotFoundError, match="Unknown tool"):
        await ToolExecutionService(registry).execute("nonexistent_tool", {}, run_id="r1")


@pytest.mark.asyncio
async def test_execute_propagates_tool_input_and_run_id() -> None:
    tool = AsyncMock()
    tool.run = AsyncMock(return_value=None)
    registry = _FakeRegistry({"web_search": tool})

    await ToolExecutionService(registry).execute("web_search", {"query": "AI"}, run_id="r1")

    tool.run.assert_called_once_with({"query": "AI"}, "r1")
