from decimal import Decimal
from typing import Any

import redis.asyncio as aioredis
import structlog
from langgraph.graph import END, START, StateGraph

from agentcore.agents.executor import execute_tool
from agentcore.agents.llm import chat, chat_json
from agentcore.agents.planner import PLANNER_SYSTEM
from agentcore.agents.state import AgentState, TaskPlan, TaskResult
from agentcore.agents.validator import VALIDATOR_SYSTEM
from agentcore.config import settings
from agentcore.guardrails.budget import BudgetExceededError, check_budget, compute_cost
from agentcore.guardrails.iterations import MaxIterationsError, check_iterations

log = structlog.get_logger()

_CHANNEL = "run:{run_id}"


async def _publish(run_id: str, event: dict[str, Any]) -> None:
    try:
        r = aioredis.from_url(settings.redis_url)
        await r.publish(_CHANNEL.format(run_id=run_id), str(event))
        await r.aclose()  # type: ignore[attr-defined]
    except Exception:
        pass  # stream failure must not break the agent


async def _planner_node(state: AgentState) -> dict[str, Any]:
    run_id = state["run_id"]
    log.info("planner_start", run_id=run_id, goal=state["goal"][:80])
    await _publish(run_id, {"type": "planner_start", "goal": state["goal"]})

    plan_raw, input_t, output_t = await chat_json(
        messages=[
            {"role": "system", "content": PLANNER_SYSTEM},
            {"role": "user", "content": f"Goal: {state['goal']}"},
        ],
        model=state["model"],
        max_tokens=1000,
        run_id=run_id,
    )

    if not isinstance(plan_raw, list):
        plan_raw = [
            {"task": state["goal"], "tool": "web_search", "tool_input": {"query": state["goal"]}}
        ]

    plan: list[TaskPlan] = [
        TaskPlan(
            task=str(t.get("task", "")),
            tool=str(t.get("tool", "web_search")),
            tool_input=t.get("tool_input", {}),
        )
        for t in plan_raw[:10]  # cap at 10 tasks
    ]

    cost = compute_cost(input_t, output_t)
    await _publish(run_id, {"type": "plan_ready", "tasks": len(plan)})

    return {
        "plan": plan,
        "current_task_index": 0,
        "input_tokens": state["input_tokens"] + input_t,
        "output_tokens": state["output_tokens"] + output_t,
        "cost_usd": float(Decimal(str(state["cost_usd"])) + cost),
        "iteration_count": state["iteration_count"] + 1,
    }


async def _executor_node(state: AgentState) -> dict[str, Any]:
    run_id = state["run_id"]
    idx = state["current_task_index"]
    plan = state["plan"]

    if idx >= len(plan):
        return {}

    task = plan[idx]
    log.info("executor_start", run_id=run_id, task=task["task"][:60], tool=task["tool"])
    await _publish(run_id, {"type": "tool_call", "tool": task["tool"], "task": task["task"]})

    try:
        check_iterations(state["iteration_count"], state["max_iterations"], run_id)
        check_budget(Decimal(str(state["cost_usd"])), state["budget_usd"], run_id)
    except (MaxIterationsError, BudgetExceededError) as exc:
        return {"error": str(exc), "status": "failed"}

    try:
        result = await execute_tool(task["tool"], task["tool_input"], run_id=run_id)
        success = True
    except Exception as exc:
        log.warning("tool_error", run_id=run_id, tool=task["tool"], error=str(exc))
        result = {"error": str(exc)}
        success = False

    task_result = TaskResult(task=task["task"], tool=task["tool"], result=result, success=success)
    await _publish(run_id, {"type": "tool_result", "tool": task["tool"], "success": success})

    return {
        "results": [*state["results"], task_result],
        "current_task_index": idx + 1,
        "iteration_count": state["iteration_count"] + 1,
        "retry_count": 0 if success else state["retry_count"] + 1,
    }


async def _validator_node(state: AgentState) -> dict[str, Any]:
    run_id = state["run_id"]
    plan = state["plan"]
    idx = state["current_task_index"]

    # More tasks remaining — continue execution
    if idx < len(plan):
        return {}

    # All tasks done — synthesize final answer
    log.info("validator_synthesize", run_id=run_id)
    await _publish(run_id, {"type": "synthesizing"})

    results_summary = "\n".join(
        f"- {r['task']}: {'✓' if r['success'] else '✗'} {str(r['result'])[:200]}"
        for r in state["results"]
    )

    answer, input_t, output_t = await chat(
        messages=[
            {"role": "system", "content": VALIDATOR_SYSTEM},
            {
                "role": "user",
                "content": (
                    f"Original goal: {state['goal']}\n\n"
                    f"Task results:\n{results_summary}\n\n"
                    "Provide a concise final answer."
                ),
            },
        ],
        model=state["model"],
        max_tokens=500,
        run_id=run_id,
    )

    cost = compute_cost(input_t, output_t)
    await _publish(run_id, {"type": "completed", "answer": answer[:200]})

    return {
        "final_answer": answer,
        "status": "completed",
        "input_tokens": state["input_tokens"] + input_t,
        "output_tokens": state["output_tokens"] + output_t,
        "cost_usd": float(Decimal(str(state["cost_usd"])) + cost),
    }


def _should_continue(state: AgentState) -> str:
    if state.get("error") or state.get("status") in ("failed", "killed"):
        return END
    if state.get("status") == "completed":
        return END
    if state["current_task_index"] < len(state["plan"]):
        return "executor"
    return END


def build_graph() -> Any:
    graph = StateGraph(AgentState)

    graph.add_node("planner", _planner_node)
    graph.add_node("executor", _executor_node)
    graph.add_node("validator", _validator_node)

    graph.add_edge(START, "planner")
    graph.add_edge("planner", "executor")
    graph.add_edge("executor", "validator")
    graph.add_conditional_edges("validator", _should_continue, {"executor": "executor", END: END})

    return graph.compile()
