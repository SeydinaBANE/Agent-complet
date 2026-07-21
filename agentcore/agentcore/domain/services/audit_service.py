"""Audit service — domain layer for agent action logging.

This service delegates persistence to an AuditPort implementation,
keeping the domain layer free of infrastructure concerns.
"""

from typing import Any

from agentcore.ports.audit_port import AuditPort


class AuditService:
    """Orchestrates audit logging through the AuditPort interface."""

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
        """Log an agent action via the configured audit port.

        Args:
            run_id: Unique identifier of the agent run.
            agent: Agent node that performed the action.
            tool: Tool name for tool calls, None for LLM calls.
            input_data: Input payload.
            output_data: Output payload, if available.
        """
        await self._audit_port.log_action(
            run_id=run_id,
            agent=agent,
            tool=tool,
            input_data=input_data,
            output_data=output_data,
        )
