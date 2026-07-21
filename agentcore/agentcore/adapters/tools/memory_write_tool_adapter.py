from typing import Any

from agentcore.ports.kv_store_port import KvStorePort

DEFAULT_TTL_SECONDS = 86400  # 24h


class MemoryWriteToolAdapter:
    name = "memory_write"

    def __init__(self, kv: KvStorePort) -> None:
        self._kv = kv

    async def run(self, tool_input: dict[str, Any], run_id: str) -> Any:
        await self._kv.set(
            str(tool_input.get("key", "")),
            str(tool_input.get("value", "")),
            int(tool_input.get("ttl", DEFAULT_TTL_SECONDS)),
        )
        return True
