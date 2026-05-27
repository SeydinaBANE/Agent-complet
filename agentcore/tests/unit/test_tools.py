from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from agentcore.guardrails.scope import ScopeViolationError
from agentcore.tools.http_caller import call_http
from agentcore.tools.memory_read import read_memory
from agentcore.tools.memory_write import write_memory


class TestHttpCaller:
    @pytest.mark.asyncio
    async def test_blocks_internal_url(self) -> None:
        with pytest.raises(ScopeViolationError):
            await call_http("http://localhost:9000/internal", run_id="r1")

    @pytest.mark.asyncio
    async def test_successful_get(self) -> None:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {"content-type": "application/json"}
        mock_response.text = '{"ok": true}'

        with patch("agentcore.tools.http_caller.httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.request = AsyncMock(
                return_value=mock_response
            )
            result = await call_http("https://example.com/api", run_id="r1")

        assert result["status_code"] == 200
        assert result["body"] == '{"ok": true}'

    @pytest.mark.asyncio
    async def test_caps_response_body(self) -> None:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {}
        mock_response.text = "x" * 10_000

        with patch("agentcore.tools.http_caller.httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.request = AsyncMock(
                return_value=mock_response
            )
            result = await call_http("https://example.com", run_id="r1")

        assert len(result["body"]) == 5000


class TestMemory:
    @pytest.mark.asyncio
    async def test_write_then_read(self) -> None:
        mock_redis = AsyncMock()
        mock_redis.get.return_value = b"hello"

        with patch("agentcore.tools.memory_read.aioredis.from_url", return_value=mock_redis):
            value = await read_memory("my_key", run_id="r1")

        assert value == "hello"
        mock_redis.get.assert_called_once_with("agent:memory:my_key")

    @pytest.mark.asyncio
    async def test_read_missing_key(self) -> None:
        mock_redis = AsyncMock()
        mock_redis.get.return_value = None

        with patch("agentcore.tools.memory_read.aioredis.from_url", return_value=mock_redis):
            value = await read_memory("missing", run_id="r1")

        assert value is None

    @pytest.mark.asyncio
    async def test_write_sets_ttl(self) -> None:
        mock_redis = AsyncMock()

        with patch("agentcore.tools.memory_write.aioredis.from_url", return_value=mock_redis):
            result = await write_memory("key", "value", ttl=3600, run_id="r1")

        assert result is True
        mock_redis.set.assert_called_once_with("agent:memory:key", "value", ex=3600)
