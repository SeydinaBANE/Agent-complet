"""Audit port — interface for persisting agent action logs.

Implementations must store every tool call and LLM interaction
for compliance, debugging, and observability.
"""

from typing import Any, Protocol


class AuditPort(Protocol):
    """Protocol for audit logging implementations."""

    async def log_action(
        self,
        run_id: str,
        agent: str,
        tool: str | None,
        input_data: dict[str, Any],
        output_data: Any | None = None,
    ) -> None:
        """Record an agent action.

        Args:
            run_id: Unique identifier of the agent run.
            agent: Agent node that performed the action (planner/executor/validator).
            tool: Tool name if the action was a tool call, None otherwise.
            input_data: Input payload sent to the agent or tool.
            output_data: Output received from the agent or tool, if any.
        """
