from unittest.mock import AsyncMock

from agentcore.adapters.langgraph.graph_factory import build_graph
from agentcore.application.services.agent_orchestrator import AgentOrchestrator


def test_build_graph_returns_compiled() -> None:
    orchestrator = AgentOrchestrator(llm=AsyncMock())
    g = build_graph(orchestrator)
    assert g is not None
