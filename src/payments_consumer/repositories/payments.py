from typing import Self
from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.core.db.models import Payment, PaymentStatus, ProcessedPayment


class PaymentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, payment_id: UUID) -> Payment | None:
        stmt = select(Payment).where(Payment.id == payment_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def update_status(self, payment_id: UUID, status: PaymentStatus) -> None:
        stmt = (
            update(Payment)
            .where(Payment.id == payment_id)
            .values(
                status=status,
                processed_at=func.now(),
            )
        )
        await self._session.execute(stmt)


class ProcessedPaymentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def try_mark_as_processed(self, payment_id: UUID) -> bool:
        stmt = (
            pg_insert(ProcessedPayment)
            .values(payment_id=payment_id)
            .on_conflict_do_nothing()
            .returning(ProcessedPayment.payment_id)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none() is not None


class ConsumerUnitOfWork:
    def __init__(self, sessionmaker: async_sessionmaker) -> None:
        self.sessionmaker = sessionmaker

    async def __aenter__(self) -> Self:
        self._session = self.sessionmaker()
        self.payment_repo = PaymentRepository(self._session)
        self.processed_repo = ProcessedPaymentRepository(self._session)
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
