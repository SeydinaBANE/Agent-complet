from typing import Any

from langgraph.graph import END, START, StateGraph

from agentcore.application.services.agent_orchestrator import AgentOrchestrator
from agentcore.domain.entities import AgentState
from agentcore.domain.services.graph_transition_policy import should_continue


def _route(state: AgentState) -> str:
    return "executor" if should_continue(state) == "continue" else END


def build_graph(orchestrator: AgentOrchestrator) -> Any:
    graph = StateGraph(AgentState)

    graph.add_node("planner", orchestrator.plan)
    graph.add_node("executor", orchestrator.execute_task)
    graph.add_node("validator", orchestrator.finalize)

    graph.add_edge(START, "planner")
    graph.add_edge("planner", "executor")
    graph.add_edge("executor", "validator")
    graph.add_conditional_edges("validator", _route, {"executor": "executor", END: END})

    return graph.compile()
