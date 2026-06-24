from abc import ABC, abstractmethod
from typing import Annotated
from uuid import UUID

from fastapi import Depends
from sqlalchemy import insert, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.db.base import get_db_session
from src.core.db.models import OutboxMessage, Payment
from src.payments_api.common.exc.exceptions import (
    PaymentNotFoundError,
)
from src.payments_api.payments.v1.dto import (
    OutboxMessageCreateDTO,
    OutboxMessageResponseDTO,
    PaymentCreateDTO,
    PaymentResponseDTO,
)


class PaymentRepoInterface(ABC):
    @abstractmethod
    async def get_or_create(
        self,
        dto: PaymentCreateDTO,
    ) -> tuple[PaymentResponseDTO, bool]: ...

    @abstractmethod
    async def get_by_id(self, payment_id: UUID) -> PaymentResponseDTO: ...


class OutboxMessageRepoInterface(ABC):
    @abstractmethod
    async def create(
        self,
        dto: OutboxMessageCreateDTO,
    ) -> OutboxMessageResponseDTO: ...


class PaymentRepository(PaymentRepoInterface):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, payment_id: UUID) -> PaymentResponseDTO:
        stmt = select(Payment).where(Payment.id == payment_id)
        result = await self._session.execute(stmt)
        row = result.scalar_one_or_none()

        if row is None:
            raise PaymentNotFoundError()

        return PaymentResponseDTO(
            id=row.id,
            amount=row.amount,
            currency=row.currency,
            description=row.description,
            meta_data=row.meta_data,
            status=row.status,
            idempotency_key=row.idempotency_key,
            webhook_url=row.webhook_url,
            created_at=row.created_at,
            processed_at=row.processed_at,
        )

    async def get_or_create(
        self,
        dto: PaymentCreateDTO,
    ) -> tuple[PaymentResponseDTO, bool]:
        stmt = pg_insert(Payment).values(
            amount=dto.amount,
            currency=dto.currency.value,
            description=dto.description,
            meta_data=dto.meta_data,
            idempotency_key=dto.idempotency_key,
            webhook_url=dto.webhook_url,
        )
        stmt = stmt.on_conflict_do_nothing(
            index_elements=[Payment.idempotency_key],
        ).returning(Payment)
        result = await self._session.execute(stmt)
        row = result.scalar_one_or_none()

        if row is not None:
            is_created = True
        else:
            select_stmt = select(Payment).where(
                Payment.idempotency_key == dto.idempotency_key,
            )
            result = await self._session.execute(select_stmt)
            row = result.scalar_one()
            is_created = False

        return PaymentResponseDTO(
            id=row.id,
            amount=row.amount,
            currency=row.currency,
            description=row.description,
            meta_data=row.meta_data,
            status=row.status,
            idempotency_key=row.idempotency_key,
            webhook_url=row.webhook_url,
            created_at=row.created_at,
            processed_at=row.processed_at,
        ), is_created


class OutboxMessageRepository(OutboxMessageRepoInterface):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, dto: OutboxMessageCreateDTO) -> OutboxMessageResponseDTO:
        stmt = (
            insert(OutboxMessage)
            .values(
                event_type=dto.event_type.value,
                payload=dto.payload,
            )
            .returning(OutboxMessage)
        )

        result = await self._session.execute(stmt)
        row = result.scalar_one()

        return OutboxMessageResponseDTO(
            id=row.id,
            event_type=row.event_type,
            status=row.status,
            payload=row.payload,
            created_at=row.created_at,
            processed_at=row.processed_at,
        )


async def get_payment_repository(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> PaymentRepoInterface:
    return PaymentRepository(session)


async def get_outbox_message_repository(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> OutboxMessageRepoInterface:
    return OutboxMessageRepository(session)
