from typing import Any

from agentcore.domain.entities import TaskPlan

MAX_TASKS = 10


def parse_plan_response(plan_raw: Any, goal: str) -> list[TaskPlan]:
    if not isinstance(plan_raw, list):
        plan_raw = [{"task": goal, "tool": "web_search", "tool_input": {"query": goal}}]

    return [
        TaskPlan(
            task=str(t.get("task", "")),
            tool=str(t.get("tool", "web_search")),
            tool_input=t.get("tool_input", {}),
        )
        for t in plan_raw[:MAX_TASKS]
    ]
