from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from agentcore.agents.llm import chat, chat_json


def _make_response(content: str, input_tokens: int = 10, output_tokens: int = 20) -> MagicMock:
    response = MagicMock()
    response.choices = [MagicMock()]
    response.choices[0].message.content = content
    response.usage = MagicMock()
    response.usage.prompt_tokens = input_tokens
    response.usage.completion_tokens = output_tokens
    return response


@pytest.mark.asyncio
async def test_chat_returns_content_and_tokens() -> None:
    mock_client = AsyncMock()
    mock_client.chat.completions.create = AsyncMock(return_value=_make_response("Hello!", 5, 3))

    with patch("agentcore.agents.llm._make_client", return_value=mock_client):
        content, input_t, output_t = await chat([{"role": "user", "content": "hi"}], "gpt-4o-mini")

    assert content == "Hello!"
    assert input_t == 5
    assert output_t == 3


@pytest.mark.asyncio
async def test_chat_json_parses_valid_json() -> None:
    mock_client = AsyncMock()
    mock_client.chat.completions.create = AsyncMock(
        return_value=_make_response('[{"task":"search","tool":"web_search","tool_input":{}}]')
    )

    with patch("agentcore.agents.llm._make_client", return_value=mock_client):
        result, _, _ = await chat_json([{"role": "user", "content": "plan"}], "gpt-4o-mini")

    assert isinstance(result, list)
    assert result[0]["task"] == "search"


@pytest.mark.asyncio
async def test_chat_json_strips_markdown_fences() -> None:
    content = '```json\n[{"task": "t", "tool": "web_search", "tool_input": {}}]\n```'
    mock_client = AsyncMock()
    mock_client.chat.completions.create = AsyncMock(return_value=_make_response(content))

    with patch("agentcore.agents.llm._make_client", return_value=mock_client):
        result, _, _ = await chat_json([{"role": "user", "content": "plan"}], "gpt-4o-mini")

    assert isinstance(result, list)


@pytest.mark.asyncio
async def test_chat_json_raises_on_invalid_json() -> None:
    mock_client = AsyncMock()
    mock_client.chat.completions.create = AsyncMock(
        return_value=_make_response("not valid json at all")
    )

    with (
        patch("agentcore.agents.llm._make_client", return_value=mock_client),
        pytest.raises(ValueError, match="LLM did not return valid JSON"),
    ):
        await chat_json([{"role": "user", "content": "plan"}], "gpt-4o-mini")


@pytest.mark.asyncio
async def test_chat_handles_none_content() -> None:
    mock_client = AsyncMock()
    response = _make_response("")
    response.choices[0].message.content = None
    mock_client.chat.completions.create = AsyncMock(return_value=response)

    with patch("agentcore.agents.llm._make_client", return_value=mock_client):
        content, _, _ = await chat([{"role": "user", "content": "hi"}], "gpt-4o-mini")

    assert content == ""
