from unittest.mock import AsyncMock

import pytest

from agentcore.adapters.tools.http_caller_tool_adapter import HttpCallerToolAdapter
from agentcore.domain.errors import ScopeViolationError
from agentcore.ports.http_client_port import HttpResponse


@pytest.mark.asyncio
async def test_run_blocks_internal_url() -> None:
    with pytest.raises(ScopeViolationError):
        await HttpCallerToolAdapter(AsyncMock()).run(
            {"url": "http://localhost:9000/internal"}, run_id="r1"
        )


@pytest.mark.asyncio
async def test_run_returns_response_for_public_url() -> None:
    http_client = AsyncMock()
    http_client.request = AsyncMock(
        return_value=HttpResponse(status_code=200, headers={}, body='{"ok": true}')
    )

    result = await HttpCallerToolAdapter(http_client).run(
        {"url": "https://example.com/api"}, run_id="r1"
    )

    assert result["status_code"] == 200
    assert result["body"] == '{"ok": true}'
