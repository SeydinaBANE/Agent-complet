from typing import Any

import structlog

log = structlog.get_logger()


async def log_action(
    run_id: str,
    agent: str,
    tool: str | None,
    input_data: dict[str, Any],
    output_data: Any | None = None,
) -> None:
    """Log agent action for debugging purposes.

    For persistent audit logging to database, use domain.services.audit_service.AuditService
    with an AuditPort implementation (e.g., SqlAlchemyAuditAdapter).
    """
    log.info(
        "agent_action",
        run_id=run_id,
        agent=agent,
        tool=tool,
        input_keys=list(input_data.keys()),
        has_output=output_data is not None,
    )
