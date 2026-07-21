from typing import Any

from agentcore.ports.kv_store_port import KvStorePort


class MemoryReadToolAdapter:
    name = "memory_read"

    def __init__(self, kv: KvStorePort) -> None:
        self._kv = kv

    async def run(self, tool_input: dict[str, Any], run_id: str) -> Any:
        return await self._kv.get(str(tool_input.get("key", "")))
