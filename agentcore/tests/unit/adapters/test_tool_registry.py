from unittest.mock import AsyncMock

import pytest

from agentcore.adapters.tools.tool_registry import StaticToolRegistry
from agentcore.domain.errors import ToolNotFoundError


def test_get_returns_registered_tool() -> None:
    tool = AsyncMock()
    registry = StaticToolRegistry({"web_search": tool})

    assert registry.get("web_search") is tool
    assert registry.list_tools() == ["web_search"]


def test_get_unknown_tool_raises() -> None:
    registry = StaticToolRegistry({})

    with pytest.raises(ToolNotFoundError, match="Unknown tool"):
        registry.get("nonexistent_tool")
