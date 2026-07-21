from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from agentcore.adapters.db.sqlalchemy_audit_adapter import SqlAlchemyAuditAdapter
from agentcore.domain.services.audit_service import AuditService


class TestAuditService:
    @pytest.mark.asyncio
    async def test_log_action_delegates_to_port(self) -> None:
        mock_port = AsyncMock()
        service = AuditService(mock_port)

        await service.log_action(
            run_id="r1",
            agent="planner",
            tool=None,
            input_data={"goal": "test"},
            output_data=None,
        )

        mock_port.log_action.assert_called_once_with(
            run_id="r1",
            agent="planner",
            tool=None,
            input_data={"goal": "test"},
            output_data=None,
        )

    @pytest.mark.asyncio
    async def test_log_action_with_output(self) -> None:
        mock_port = AsyncMock()
        service = AuditService(mock_port)
        output: dict[str, Any] = {"results": []}

        await service.log_action(
            run_id="r1",
            agent="executor",
            tool="web_search",
            input_data={"query": "AI"},
            output_data=output,
        )

        mock_port.log_action.assert_called_once_with(
            run_id="r1",
            agent="executor",
            tool="web_search",
            input_data={"query": "AI"},
            output_data=output,
        )


class TestSqlAlchemyAuditAdapter:
    @pytest.mark.asyncio
    async def test_log_action_persists_action(self) -> None:
        mock_session = MagicMock()
        mock_session.flush = AsyncMock()
        adapter = SqlAlchemyAuditAdapter(mock_session)

        await adapter.log_action(
            run_id="r1",
            agent="planner",
            tool=None,
            input_data={"goal": "test"},
            output_data=None,
        )

        mock_session.add.assert_called_once()
        mock_session.flush.assert_called_once()

    @pytest.mark.asyncio
    async def test_log_action_with_output_persists(self) -> None:
        mock_session = MagicMock()
        mock_session.flush = AsyncMock()
        adapter = SqlAlchemyAuditAdapter(mock_session)

        await adapter.log_action(
            run_id="r1",
            agent="executor",
            tool="web_search",
            input_data={"query": "AI"},
            output_data={"results": []},
        )

        mock_session.add.assert_called_once()
        mock_session.flush.assert_called_once()
