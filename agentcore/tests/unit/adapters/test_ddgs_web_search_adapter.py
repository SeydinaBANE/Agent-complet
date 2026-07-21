from unittest.mock import MagicMock, patch

import pytest

from agentcore.adapters.tools.ddgs_web_search_adapter import DdgsWebSearchAdapter


@pytest.mark.asyncio
async def test_search_returns_list() -> None:
    mock_results = [
        {"title": "Result 1", "href": "https://example.com/1", "body": "Snippet 1"},
        {"title": "Result 2", "href": "https://example.com/2", "body": "Snippet 2"},
    ]
    mock_ddgs = MagicMock()
    mock_ddgs.__enter__ = MagicMock(return_value=mock_ddgs)
    mock_ddgs.__exit__ = MagicMock(return_value=False)
    mock_ddgs.text = MagicMock(return_value=mock_results)

    with patch("agentcore.adapters.tools.ddgs_web_search_adapter.DDGS", return_value=mock_ddgs):
        results = await DdgsWebSearchAdapter().search("AI agents", max_results=2)

    assert len(results) == 2
    assert results[0]["title"] == "Result 1"
    assert results[0]["url"] == "https://example.com/1"
    assert results[0]["snippet"] == "Snippet 1"


@pytest.mark.asyncio
async def test_search_empty_results() -> None:
    mock_ddgs = MagicMock()
    mock_ddgs.__enter__ = MagicMock(return_value=mock_ddgs)
    mock_ddgs.__exit__ = MagicMock(return_value=False)
    mock_ddgs.text = MagicMock(return_value=[])

    with patch("agentcore.adapters.tools.ddgs_web_search_adapter.DDGS", return_value=mock_ddgs):
        results = await DdgsWebSearchAdapter().search("nothing", max_results=5)

    assert results == []
