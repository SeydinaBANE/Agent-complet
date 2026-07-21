from typing import Any

import structlog

from agentcore.ports.tool_registry_port import ToolRegistryPort

log = structlog.get_logger()


class ToolExecutionService:
    def __init__(self, tools: ToolRegistryPort) -> None:
        self._tools = tools

    async def execute(self, tool: str, tool_input: dict[str, Any], run_id: str) -> Any:
        adapter = self._tools.get(tool)
        log.info("tool_executing", run_id=run_id, tool=tool)
        result = await adapter.run(tool_input, run_id)
        log.info("tool_executed", run_id=run_id, tool=tool)
        return result
