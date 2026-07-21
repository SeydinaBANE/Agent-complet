import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from agentcore.adapters.db.sqlalchemy_run_repository import SqlAlchemyRunRepository
from agentcore.db.models import Run


def _mock_session() -> AsyncMock:
    session = AsyncMock()
    session.add = MagicMock()
    session.commit = AsyncMock()
    session.execute = AsyncMock()
    return session


@pytest.mark.asyncio
async def test_create_persists_pending_run() -> None:
    session = _mock_session()
    run_id = str(uuid.uuid4())

    await SqlAlchemyRunRepository(session).create(run_id, "goal", "openai/gpt-4o-mini")

    session.add.assert_called_once()
    session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_by_id_returns_none_when_missing() -> None:
    session = _mock_session()
    session.execute = AsyncMock(
        return_value=MagicMock(scalar_one_or_none=MagicMock(return_value=None))
    )

    record = await SqlAlchemyRunRepository(session).get_by_id(str(uuid.uuid4()))

    assert record is None


@pytest.mark.asyncio
async def test_get_by_id_maps_run_to_record() -> None:
    session = _mock_session()
    run = Run(
        id=uuid.uuid4(),
        goal="find LLM frameworks",
        model="openai/gpt-4o-mini",
        status="completed",
    )
    session.execute = AsyncMock(
        return_value=MagicMock(scalar_one_or_none=MagicMock(return_value=run))
    )

    record = await SqlAlchemyRunRepository(session).get_by_id(str(run.id))

    assert record is not None
    assert record.id == str(run.id)
    assert record.goal == "find LLM frameworks"
    assert record.status == "completed"


@pytest.mark.asyncio
async def test_list_ignores_invalid_cursor() -> None:
    session = _mock_session()
    session.execute = AsyncMock(
        return_value=MagicMock(
            scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[])))
        )
    )

    records = await SqlAlchemyRunRepository(session).list(cursor="not-a-uuid", limit=20)

    assert records == []
