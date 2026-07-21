"""SQLAlchemy audit adapter — AuditPort implementation.

Persists agent actions to the ``actions`` PostgreSQL table.
Each record captures the run, agent node, tool name, and
input/output payloads as JSONB.
"""

from typing import Any

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from agentcore.db.models import Action

log = structlog.get_logger()


class SqlAlchemyAuditAdapter:
    """AuditPort that writes to PostgreSQL via SQLAlchemy."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def log_action(
        self,
        run_id: str,
        agent: str,
        tool: str | None,
        input_data: dict[str, Any],
        output_data: Any | None = None,
    ) -> None:
        """Insert an action record into the database.

        Args:
            run_id: Foreign key to the parent run.
            agent: Agent node name (planner/executor/validator).
            tool: Tool name, or None for LLM-only actions.
            input_data: Input payload stored as JSONB.
            output_data: Output payload stored as JSONB, if any.
        """
        action = Action(
            run_id=run_id,
            agent=agent,
            tool=tool,
            input=input_data,
            output=output_data,
        )
        self._session.add(action)
        await self._session.flush()
        log.info(
            "action_logged",
            run_id=run_id,
            agent=agent,
            tool=tool,
            input_keys=list(input_data.keys()),
            has_output=output_data is not None,
        )
