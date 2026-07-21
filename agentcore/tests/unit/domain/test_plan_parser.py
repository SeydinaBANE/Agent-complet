from agentcore.domain.services.plan_parser import parse_plan_response


def test_parse_plan_response_normalizes_list() -> None:
    plan_raw = [
        {"task": "search frameworks", "tool": "web_search", "tool_input": {"query": "Python LLM"}}
    ]

    plan = parse_plan_response(plan_raw, goal="find the best Python LLM framework")

    assert len(plan) == 1
    assert plan[0]["tool"] == "web_search"


def test_parse_plan_response_falls_back_on_non_list() -> None:
    plan = parse_plan_response({"bad": "response"}, goal="find the best Python LLM framework")

    assert len(plan) == 1
    assert plan[0]["tool"] == "web_search"
    assert plan[0]["task"] == "find the best Python LLM framework"


def test_parse_plan_response_caps_at_ten_tasks() -> None:
    plan_raw = [{"task": f"t{i}", "tool": "web_search", "tool_input": {}} for i in range(20)]

    plan = parse_plan_response(plan_raw, goal="goal")

    assert len(plan) == 10
