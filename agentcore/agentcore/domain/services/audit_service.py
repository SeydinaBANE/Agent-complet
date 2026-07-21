from typing import Any

from agentcore.ports.audit_port import AuditPort


class AuditService:
    def __init__(self, audit_port: AuditPort) -> None:
        self._audit_port = audit_port

    async def log_action(
        self,
        run_id: str,
        agent: str,
        tool: str | None,
        input_data: dict[str, Any],
        output_data: Any | None = None,
    ) -> None:
        await self._audit_port.log_action(
            run_id=run_id,
            agent=agent,
            tool=tool,
            input_data=input_data,
            output_data=output_data,
        )
