from typing import Any

from agentcore.ports.web_search_port import WebSearchPort

DEFAULT_MAX_RESULTS = 5


class WebSearchToolAdapter:
    name = "web_search"

    def __init__(self, web_search: WebSearchPort) -> None:
        self._web_search = web_search

    async def run(self, tool_input: dict[str, Any], run_id: str) -> Any:
        return await self._web_search.search(
            query=str(tool_input.get("query", "")),
            max_results=int(tool_input.get("max_results", DEFAULT_MAX_RESULTS)),
        )
