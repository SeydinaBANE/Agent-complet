from typing import Any

from agentcore.ports.kv_store_port import KvStorePort

DEFAULT_TTL_SECONDS = 86400  # 24h
MAX_VALUE_SIZE = 1024 * 100  # 100 KB


class MemoryWriteToolAdapter:
    name = "memory_write"

    def __init__(self, kv: KvStorePort) -> None:
        self._kv = kv

    async def run(self, tool_input: dict[str, Any], run_id: str) -> Any:
        key = str(tool_input.get("key", ""))
        value = str(tool_input.get("value", ""))
        ttl = int(tool_input.get("ttl", DEFAULT_TTL_SECONDS))

        if len(value) > MAX_VALUE_SIZE:
            value = value[:MAX_VALUE_SIZE]

        await self._kv.set(key, value, ttl)
        return True
