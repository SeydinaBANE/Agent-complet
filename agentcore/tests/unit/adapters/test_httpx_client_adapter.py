from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from agentcore.adapters.http.httpx_client_adapter import HttpxClientAdapter


@pytest.mark.asyncio
async def test_request_returns_response() -> None:
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.headers = {"content-type": "application/json"}
    mock_response.text = '{"ok": true}'

    with patch("agentcore.adapters.http.httpx_client_adapter.httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.request = AsyncMock(
            return_value=mock_response
        )
        response = await HttpxClientAdapter().request("GET", "https://example.com/api")

    assert response.status_code == 200
    assert response.body == '{"ok": true}'


@pytest.mark.asyncio
async def test_request_caps_response_body() -> None:
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.headers = {}
    mock_response.text = "x" * 10_000

    with patch("agentcore.adapters.http.httpx_client_adapter.httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.request = AsyncMock(
            return_value=mock_response
        )
        response = await HttpxClientAdapter().request("GET", "https://example.com")

    assert len(response.body) == 5000
