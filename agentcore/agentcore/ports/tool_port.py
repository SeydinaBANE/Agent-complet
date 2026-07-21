from typing import Any, Protocol


class ToolPort(Protocol):
    @property
    def name(self) -> str: ...

    async def run(self, tool_input: dict[str, Any], run_id: str) -> Any: ...
