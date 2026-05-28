from typing import Any

from fastapi import APIRouter, Depends

from agentcore.api.deps import require_api_key

router = APIRouter(tags=["tools"])

AVAILABLE_TOOLS = [
    {"name": "web_search", "description": "Search the web using DuckDuckGo"},
    {"name": "http_caller", "description": "Make arbitrary HTTP GET/POST requests"},
    {"name": "memory_read", "description": "Read from persistent agent memory (Redis)"},
    {"name": "memory_write", "description": "Write to persistent agent memory (Redis)"},
]


@router.get("/tools", dependencies=[Depends(require_api_key)])
async def list_tools() -> list[dict[str, Any]]:
    return AVAILABLE_TOOLS
