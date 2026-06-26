from decimal import Decimal
from typing import Annotated
from uuid import UUID

from fastapi import Depends
from sqlalchemy.exc import DBAPIError, OperationalError

from src.core.db.models import Currency, OutboxMessageType
from src.core.utils.backoff import Backoff
from src.payments_api.payments.v1.dto import (
    OutboxMessageCreateDTO,
    PaymentCreateDTO,
    PaymentResponseDTO,
)
from src.payments_api.payments.v1.interfaces import PaymentsUnitOfWorkInterface
from src.payments_api.payments.v1.repository import (
    get_payment_uow,
)


class PaymentService:
    def __init__(
        self,
        uow: PaymentsUnitOfWorkInterface,
    ) -> None:
        self._uow = uow

    @Backoff(exceptions=(OperationalError, DBAPIError))
    async def create_payment(
        self,
        amount: Decimal,
        currency: Currency,
        idempotency_key: str,
        webhook_url: str,
        description: str | None = None,
        meta_data: dict | None = None,
    ) -> PaymentResponseDTO:
        async with self._uow as uow:
            payment_dto = PaymentCreateDTO(
                amount=amount,
                currency=currency,
                idempotency_key=idempotency_key,
                webhook_url=webhook_url,
                description=description,
                meta_data=meta_data,
            )
            payment, is_created = await uow.payment_repo.get_or_create(
                payment_dto,
            )
            if is_created:
                outbox_dto = OutboxMessageCreateDTO(
                    event_type=OutboxMessageType.PAYMENT_CREATED,
                    payload={"payment_id": str(payment.id)},
                )
                await uow.outbox_repo.create(outbox_dto)

            await uow.commit()

            return payment

    async def get_payment(self, payment_id: UUID) -> PaymentResponseDTO:
        async with self._uow as uow:
            return await uow.payment_repo.get_by_id(payment_id)


async def get_payment_service(
    uow: Annotated[PaymentsUnitOfWorkInterface, Depends(get_payment_uow)],
) -> PaymentService:
    return PaymentService(uow=uow)
