from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from agentcore.agents.validator import build_validator, validate_result


def test_build_validator_returns_llm() -> None:
    llm = build_validator("openai/gpt-4o-mini")
    assert llm is not None


@pytest.mark.asyncio
async def test_validate_result_returns_decision() -> None:
    mock_response = MagicMock()
    mock_response.content = '{"decision": "complete", "reason": "done"}'

    mock_llm = AsyncMock()
    mock_llm.ainvoke = AsyncMock(return_value=mock_response)

    with patch("agentcore.agents.validator.build_validator", return_value=mock_llm):
        result = await validate_result(
            task="search for AI news",
            result={"results": ["article1"]},
            model="openai/gpt-4o-mini",
            run_id="r1",
        )

    assert result["decision"] == "complete"


@pytest.mark.asyncio
async def test_validate_truncates_long_result() -> None:
    mock_response = MagicMock()
    mock_response.content = '{"decision": "complete", "reason": "ok"}'

    mock_llm = AsyncMock()
    mock_llm.ainvoke = AsyncMock(return_value=mock_response)

    long_result = "x" * 10_000

    with patch("agentcore.agents.validator.build_validator", return_value=mock_llm):
        result = await validate_result("task", long_result, "openai/gpt-4o-mini", "r1")

    assert result is not None
    call_args = mock_llm.ainvoke.call_args[0][0]
    user_message = call_args[1]["content"]
    assert len(user_message) < 2000  # truncated to 500 chars of result
