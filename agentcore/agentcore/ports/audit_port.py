from typing import Any, Protocol


class AuditPort(Protocol):
    async def log_action(
        self,
        run_id: str,
        agent: str,
        tool: str | None,
        input_data: dict[str, Any],
        output_data: Any | None = None,
    ) -> None: ...
