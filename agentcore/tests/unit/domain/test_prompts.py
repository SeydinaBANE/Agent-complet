from agentcore.domain.prompts import PLANNER_SYSTEM


def test_planner_system_prompt_contains_tools() -> None:
    assert "web_search" in PLANNER_SYSTEM
    assert "http_caller" in PLANNER_SYSTEM
    assert "memory_read" in PLANNER_SYSTEM
