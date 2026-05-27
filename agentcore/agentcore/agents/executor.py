from collections.abc import Awaitable, Callable
from typing import Any

import structlog

from agentcore.tools.http_caller import call_http
from agentcore.tools.memory_read import read_memory
from agentcore.tools.memory_write import write_memory
from agentcore.tools.web_search import search_web

log = structlog.get_logger()

ToolFn = Callable[..., Awaitable[Any]]

TOOL_REGISTRY: dict[str, ToolFn] = {
    "web_search": search_web,
    "http_caller": call_http,
    "memory_read": read_memory,
    "memory_write": write_memory,
}


async def execute_tool(tool: str, tool_input: dict[str, Any], run_id: str) -> Any:
    if tool not in TOOL_REGISTRY:
        raise ValueError(f"Unknown tool: {tool}")

    log.info("tool_executing", run_id=run_id, tool=tool)
    result = await TOOL_REGISTRY[tool](**tool_input)
    log.info("tool_executed", run_id=run_id, tool=tool)
    return result
