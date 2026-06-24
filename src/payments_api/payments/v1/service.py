from decimal import Decimal
from typing import Annotated
from uuid import UUID

from fastapi import Depends

from src.core.db.models import Currency, OutboxMessageType
from src.payments_api.payments.v1.dto import (
    OutboxMessageCreateDTO,
    PaymentCreateDTO,
    PaymentResponseDTO,
)
from src.payments_api.payments.v1.repository import (
    OutboxMessageRepoInterface,
    PaymentRepoInterface,
    get_outbox_message_repository,
    get_payment_repository,
)


class PaymentService:
    def __init__(
        self,
        payment_repo: PaymentRepoInterface,
        outbox_repo: OutboxMessageRepoInterface,
    ) -> None:
        self._payment_repo = payment_repo
        self._outbox_repo = outbox_repo

    async def create_payment(
        self,
        amount: Decimal,
        currency: Currency,
        idempotency_key: str,
        webhook_url: str,
        description: str | None = None,
        meta_data: dict | None = None,
    ) -> PaymentResponseDTO:
        payment_dto = PaymentCreateDTO(
            amount=amount,
            currency=currency,
            idempotency_key=idempotency_key,
            webhook_url=webhook_url,
            description=description,
            meta_data=meta_data,
        )
        payment, is_created = await self._payment_repo.get_or_create(payment_dto)
        if is_created:
            outbox_dto = OutboxMessageCreateDTO(
                event_type=OutboxMessageType.PAYMENT_CREATED,
                payload={"payment_id": str(payment.id)},
            )
            await self._outbox_repo.create(outbox_dto)

        return payment

    async def get_payment(self, payment_id: UUID) -> PaymentResponseDTO:
        return await self._payment_repo.get_by_id(payment_id)


async def get_payment_service(
    payment_repo: Annotated[
        PaymentRepoInterface,
        Depends(get_payment_repository),
    ],
    outbox_repo: Annotated[
        OutboxMessageRepoInterface,
        Depends(get_outbox_message_repository),
    ],
) -> PaymentService:
    return PaymentService(payment_repo, outbox_repo)
