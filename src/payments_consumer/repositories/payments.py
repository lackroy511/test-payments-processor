from datetime import datetime
from typing import Self, Sequence
from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.core.db.models import Payment, PaymentStatus


class PaymentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, payment_id: UUID) -> Payment | None:
        stmt = select(Payment).where(Payment.id == payment_id).with_for_update()
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def update_payment(
        self,
        payment_id: UUID | None = None,
        external_id: str | None = None,
        status: PaymentStatus | None = None,
        *,
        is_processed: bool | None = None,
        is_webhook_sent: bool | None = None,
    ) -> None:
        stmt = (
            update(Payment)
            .where(Payment.id == payment_id)
        )
        if external_id is not None:
            stmt = stmt.values(external_id=external_id)
        
        if status is not None:
            stmt = stmt.values(status=status)
        
        if is_processed is not None:
            stmt = stmt.values(is_processed=is_processed, processed_at=func.now())
        
        if is_webhook_sent is not None:
            stmt = stmt.values(is_webhook_sent=is_webhook_sent)
        
        await self._session.execute(stmt)

    async def get_processed_payments_for_webhook(
        self,
        is_webhook_sent: bool,
        processed_after: datetime,
        limit: int = 10,
    ) -> Sequence[Payment]:
        stmt = (
            select(Payment)
            .where(
                Payment.is_processed.is_(True),
                Payment.is_webhook_sent.is_(is_webhook_sent),
                Payment.processed_at >= processed_after,
            )
            .limit(limit)
            .with_for_update(skip_locked=True)
        )
        result = await self._session.execute(stmt)
        return result.scalars().all()


class ConsumerUnitOfWork:
    def __init__(self, sessionmaker: async_sessionmaker) -> None:
        self.sessionmaker = sessionmaker

    async def __aenter__(self) -> Self:
        self._session = self.sessionmaker()
        self.payment_repo = PaymentRepository(self._session)
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
