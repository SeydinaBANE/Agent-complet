from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from agentcore.adapters.llm.openrouter_llm_adapter import OpenRouterLlmAdapter


def _make_response(content: str, input_tokens: int = 10, output_tokens: int = 20) -> MagicMock:
    response = MagicMock()
    response.choices = [MagicMock()]
    response.choices[0].message.content = content
    response.usage = MagicMock()
    response.usage.prompt_tokens = input_tokens
    response.usage.completion_tokens = output_tokens
    return response


def _adapter_with_mock_client() -> tuple[OpenRouterLlmAdapter, AsyncMock]:
    adapter = OpenRouterLlmAdapter(api_key="key", base_url="https://openrouter.ai/api/v1")
    mock_client = AsyncMock()
    adapter._client = mock_client
    return adapter, mock_client


@pytest.mark.asyncio
async def test_chat_returns_content_and_tokens() -> None:
    adapter, mock_client = _adapter_with_mock_client()
    mock_client.chat.completions.create = AsyncMock(return_value=_make_response("Hello!", 5, 3))

    content, input_t, output_t = await adapter.chat(
        [{"role": "user", "content": "hi"}], "gpt-4o-mini", 1000, "r1"
    )

    assert content == "Hello!"
    assert input_t == 5
    assert output_t == 3


@pytest.mark.asyncio
async def test_chat_handles_none_content() -> None:
    adapter, mock_client = _adapter_with_mock_client()
    response = _make_response("")
    response.choices[0].message.content = None
    mock_client.chat.completions.create = AsyncMock(return_value=response)

    content, _, _ = await adapter.chat(
        [{"role": "user", "content": "hi"}], "gpt-4o-mini", 1000, "r1"
    )

    assert content == ""


@pytest.mark.asyncio
async def test_chat_json_parses_valid_json() -> None:
    adapter, mock_client = _adapter_with_mock_client()
    mock_client.chat.completions.create = AsyncMock(
        return_value=_make_response('[{"task":"search","tool":"web_search","tool_input":{}}]')
    )

    result, _, _ = await adapter.chat_json(
        [{"role": "user", "content": "plan"}], "gpt-4o-mini", 1000, "r1"
    )

    assert isinstance(result, list)
    assert result[0]["task"] == "search"


@pytest.mark.asyncio
async def test_chat_json_strips_markdown_fences() -> None:
    adapter, mock_client = _adapter_with_mock_client()
    content = '```json\n[{"task": "t", "tool": "web_search", "tool_input": {}}]\n```'
    mock_client.chat.completions.create = AsyncMock(return_value=_make_response(content))

    result, _, _ = await adapter.chat_json(
        [{"role": "user", "content": "plan"}], "gpt-4o-mini", 1000, "r1"
    )

    assert isinstance(result, list)


@pytest.mark.asyncio
async def test_chat_json_raises_on_invalid_json() -> None:
    adapter, mock_client = _adapter_with_mock_client()
    mock_client.chat.completions.create = AsyncMock(
        return_value=_make_response("not valid json at all")
    )

    with pytest.raises(ValueError, match="LLM did not return valid JSON"):
        await adapter.chat_json([{"role": "user", "content": "plan"}], "gpt-4o-mini", 1000, "r1")


@pytest.mark.asyncio
async def test_openrouter_llm_adapter_builds_client_once() -> None:
    with patch("agentcore.adapters.llm.openrouter_llm_adapter.AsyncOpenAI") as mock_ctor:
        adapter = OpenRouterLlmAdapter(api_key="key", base_url="https://openrouter.ai/api/v1")
        assert adapter._client is mock_ctor.return_value
        mock_ctor.assert_called_once_with(api_key="key", base_url="https://openrouter.ai/api/v1")
