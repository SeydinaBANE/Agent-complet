from agentcore.domain.errors import ToolNotFoundError
from agentcore.ports.tool_port import ToolPort


class StaticToolRegistry:
    def __init__(self, tools: dict[str, ToolPort]) -> None:
        self._tools = tools

    def get(self, name: str) -> ToolPort:
        if name not in self._tools:
            raise ToolNotFoundError(f"Unknown tool: {name}")
        return self._tools[name]

    def list_tools(self) -> list[str]:
        return list(self._tools.keys())
