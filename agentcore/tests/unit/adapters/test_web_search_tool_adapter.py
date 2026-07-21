from unittest.mock import AsyncMock

import pytest

from agentcore.adapters.tools.web_search_tool_adapter import WebSearchToolAdapter


@pytest.mark.asyncio
async def test_run_dispatches_to_web_search_port() -> None:
    web_search = AsyncMock()
    web_search.search = AsyncMock(return_value=[{"title": "t", "url": "u", "snippet": "s"}])

    result = await WebSearchToolAdapter(web_search).run({"query": "AI"}, run_id="r1")

    web_search.search.assert_called_once_with(query="AI", max_results=5)
    assert result == [{"title": "t", "url": "u", "snippet": "s"}]


@pytest.mark.asyncio
async def test_run_defaults_missing_query_to_empty_string() -> None:
    web_search = AsyncMock()
    web_search.search = AsyncMock(return_value=[])

    await WebSearchToolAdapter(web_search).run({}, run_id="r1")

    web_search.search.assert_called_once_with(query="", max_results=5)
