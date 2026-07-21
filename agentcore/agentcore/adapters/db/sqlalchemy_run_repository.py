import contextlib
import uuid
from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from agentcore.db.models import Run
from agentcore.domain.entities import RunRecord


def _to_record(run: Run) -> RunRecord:
    return RunRecord(
        id=str(run.id),
        goal=run.goal,
        model=run.model,
        status=run.status,
        iteration_count=run.iteration_count,
        input_tokens=run.input_tokens,
        output_tokens=run.output_tokens,
        cost_usd=run.cost_usd,
        error=run.error,
        started_at=run.started_at,
    )


class SqlAlchemyRunRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, run_id: str, goal: str, model: str) -> None:
        run = Run(id=uuid.UUID(run_id), goal=goal, model=model, status="pending")
        self._session.add(run)
        await self._session.commit()

    async def mark_running(self, run_id: str) -> None:
        await self._session.execute(
            update(Run)
            .where(Run.id == uuid.UUID(run_id))
            .values(status="running", started_at=datetime.now(UTC))
        )
        await self._session.commit()

    async def mark_finished(
        self,
        run_id: str,
        status: str,
        iteration_count: int,
        input_tokens: int,
        output_tokens: int,
        cost_usd: float,
        error: str | None,
    ) -> None:
        await self._session.execute(
            update(Run)
            .where(Run.id == uuid.UUID(run_id))
            .values(
                status=status,
                finished_at=datetime.now(UTC),
                iteration_count=iteration_count,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                cost_usd=Decimal(str(cost_usd)),
                error=error,
            )
        )
        await self._session.commit()

    async def get_by_id(self, run_id: str) -> RunRecord | None:
        result = await self._session.execute(select(Run).where(Run.id == uuid.UUID(run_id)))
        run = result.scalar_one_or_none()
        return _to_record(run) if run else None

    async def list(self, cursor: str | None, limit: int) -> list[RunRecord]:
        query = select(Run).order_by(Run.created_at.desc()).limit(min(limit, 100))
        if cursor:
            with contextlib.suppress(ValueError):
                query = query.where(Run.id < uuid.UUID(cursor))

        result = await self._session.execute(query)
        return [_to_record(run) for run in result.scalars().all()]
