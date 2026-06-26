from typing import Self
from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.core.db.models import OutboxMessage, OutboxMessageStatus
from src.payments_publisher.repositories.dto import OutboxMessageDTO


class PublisherOutboxRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_pending_batch(self, limit: int = 100) -> list[OutboxMessageDTO]:
        stmt = (
            select(OutboxMessage)
            .where(OutboxMessage.status == OutboxMessageStatus.PENDING)
            .limit(limit)
            .order_by(OutboxMessage.created_at.asc())
            .with_for_update(skip_locked=True)
        )
        result = await self._session.execute(stmt)
        rows = result.scalars().all()

        return [
            OutboxMessageDTO(
                id=row.id,
                event_type=row.event_type,
                status=row.status,
                payload=row.payload,
                created_at=row.created_at,
                processed_at=row.processed_at,
            )
            for row in rows
        ]

    async def mark_as_published(self, message_id: UUID) -> None:
        stmt = (
            update(OutboxMessage)
            .where(OutboxMessage.id == message_id)
            .values(status=OutboxMessageStatus.PUBLISHED, processed_at=func.now())
        )
        await self._session.execute(stmt)


class PublisherUnitOfWork:
    def __init__(self, sessionmaker: async_sessionmaker) -> None:
        self.sessionmaker = sessionmaker

    async def __aenter__(self) -> Self:
        self._session = self.sessionmaker()
        self.outbox_repo = PublisherOutboxRepository(self._session)
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: object | None,
    ) -> None:
        if exc_type is not None:
            await self.rollback()

        await self._session.close()

    async def commit(self) -> None:
        await self._session.commit()

    async def rollback(self) -> None:
        await self._session.rollback()
