from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from agentcore.adapters.http.httpx_client_adapter import HttpxClientAdapter


@pytest.mark.asyncio
async def test_request_returns_response() -> None:
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.headers = {"content-type": "application/json"}
    mock_response.text = '{"ok": true}'

    mock_client = AsyncMock()
    mock_client.request = AsyncMock(return_value=mock_response)

    with patch(
        "agentcore.adapters.http.httpx_client_adapter._get_client",
        new_callable=AsyncMock,
        return_value=mock_client,
    ):
        response = await HttpxClientAdapter().request("GET", "https://example.com/api")

    assert response.status_code == 200
    assert response.body == '{"ok": true}'


@pytest.mark.asyncio
async def test_request_caps_response_body() -> None:
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.headers = {}
    mock_response.text = "x" * 10_000

    mock_client = AsyncMock()
    mock_client.request = AsyncMock(return_value=mock_response)

    with patch(
        "agentcore.adapters.http.httpx_client_adapter._get_client",
        new_callable=AsyncMock,
        return_value=mock_client,
    ):
        response = await HttpxClientAdapter().request("GET", "https://example.com")

    assert len(response.body) == 5000
