from agentcore.domain.entities import AgentState


def should_continue(state: AgentState) -> str:
    if state.get("error") or state.get("status") in ("failed", "killed"):
        return "stop"
    if state.get("status") == "completed":
        return "stop"
    if state["current_task_index"] < len(state["plan"]):
        return "continue"
    return "stop"
