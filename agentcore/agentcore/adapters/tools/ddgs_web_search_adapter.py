from typing import Any

from duckduckgo_search import DDGS


class DdgsWebSearchAdapter:
    async def search(self, query: str, max_results: int = 5) -> list[dict[str, Any]]:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))
        return [{"title": r["title"], "url": r["href"], "snippet": r["body"]} for r in results]
