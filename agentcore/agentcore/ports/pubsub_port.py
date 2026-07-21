from collections.abc import AsyncGenerator
from typing import Any, Protocol


class PubSubPort(Protocol):
    async def publish(self, run_id: str, event: dict[str, Any]) -> None: ...

    def subscribe(self, run_id: str) -> AsyncGenerator[dict[str, Any], None]: ...
