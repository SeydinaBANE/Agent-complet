import pytest

from agentcore.guardrails.audit import log_action


@pytest.mark.asyncio
async def test_log_action_no_output() -> None:
    await log_action("r1", "planner", None, {"goal": "test"})


@pytest.mark.asyncio
async def test_log_action_with_output() -> None:
    await log_action("r1", "executor", "web_search", {"query": "AI"}, {"results": []})


@pytest.mark.asyncio
async def test_log_action_with_empty_input() -> None:
    await log_action("r1", "validator", None, {})
