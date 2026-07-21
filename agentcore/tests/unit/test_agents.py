from unittest.mock import AsyncMock, patch

import pytest

from agentcore.agents.executor import execute_tool
from agentcore.domain.prompts import PLANNER_SYSTEM


class TestExecutor:
    @pytest.mark.asyncio
    async def test_unknown_tool_raises(self) -> None:
        with pytest.raises(ValueError, match="Unknown tool"):
            await execute_tool("nonexistent_tool", {}, run_id="r1")

    @pytest.mark.asyncio
    async def test_web_search_dispatched(self) -> None:
        expected = [{"title": "t", "url": "u", "snippet": "s"}]
        # Patch TOOL_REGISTRY directly — it holds references captured at import time
        with patch(
            "agentcore.agents.executor.TOOL_REGISTRY",
            {"web_search": AsyncMock(return_value=expected)},
        ):
            result = await execute_tool("web_search", {"query": "AI"}, run_id="r1")
        assert result == expected

    @pytest.mark.asyncio
    async def test_memory_read_dispatched(self) -> None:
        mock_read = AsyncMock(return_value="cached")
        with patch("agentcore.agents.executor.TOOL_REGISTRY", {"memory_read": mock_read}):
            result = await execute_tool("memory_read", {"key": "k"}, run_id="r1")
        assert result == "cached"

    @pytest.mark.asyncio
    async def test_memory_write_dispatched(self) -> None:
        mock_write = AsyncMock(return_value=True)
        with patch("agentcore.agents.executor.TOOL_REGISTRY", {"memory_write": mock_write}):
            result = await execute_tool("memory_write", {"key": "k", "value": "v"}, run_id="r1")
        assert result is True

    @pytest.mark.asyncio
    async def test_http_caller_dispatched(self) -> None:
        expected = {"status_code": 200, "headers": {}, "body": "ok"}
        mock_http = AsyncMock(return_value=expected)
        with patch("agentcore.agents.executor.TOOL_REGISTRY", {"http_caller": mock_http}):
            result = await execute_tool("http_caller", {"url": "https://x.com"}, run_id="r1")
        assert result["status_code"] == 200


class TestPlanner:
    def test_planner_system_prompt_contains_tools(self) -> None:
        assert "web_search" in PLANNER_SYSTEM
        assert "http_caller" in PLANNER_SYSTEM
        assert "memory_read" in PLANNER_SYSTEM
