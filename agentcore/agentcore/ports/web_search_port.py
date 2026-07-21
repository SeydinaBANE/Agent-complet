from typing import Any, Protocol


class WebSearchPort(Protocol):
    async def search(self, query: str, max_results: int) -> list[dict[str, Any]]: ...
