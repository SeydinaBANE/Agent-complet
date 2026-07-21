from typing import Protocol

from agentcore.ports.tool_port import ToolPort


class ToolRegistryPort(Protocol):
    def get(self, name: str) -> ToolPort: ...

    def list_tools(self) -> list[str]: ...
