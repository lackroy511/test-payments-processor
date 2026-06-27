from decimal import Decimal
import asyncio
import logging
import random
from uuid import UUID, uuid7

import httpx
from sqlalchemy.exc import DBAPIError, OperationalError

from src.core.db.models import PaymentStatus, Currency
from src.core.utils.backoff import Backoff
from src.payments_consumer.repositories.payments import ConsumerUnitOfWork

log = logging.getLogger(__name__)


class ConsumerService:
    def __init__(self, uow: ConsumerUnitOfWork) -> None:
        self._uow = uow

    @Backoff(exceptions=(OperationalError, DBAPIError, httpx.HTTPError))
    async def process_payment(self, payment_id: UUID) -> None:
        async with self._uow as uow:
            payment = await uow.payment_repo.get_by_id(payment_id)
            if payment is None:
                log.warning("Payment %r not found:", payment_id)
                return

            if payment.status == PaymentStatus.PENDING:
                new_status, external_id = await self._process_in_payment_gateway(
                    payment.id,
                    payment.idempotency_key,
                    payment.amount,
                    payment.currency,
                )

                await uow.payment_repo.update_payment(
                    payment_id,
                    external_id,
                    new_status,
                    is_processed=True,
                    is_webhook_sent=False,
                )
                await uow.commit()

    async def _process_in_payment_gateway(
        self,
        payment_id: UUID,
        idempotency_key: str,
        amount: Decimal,
        currency: Currency,
    ) -> tuple[PaymentStatus, str]:
        # headers = {
        #     "Idempotency-Key": idempotency_key,
        #     ...
        # }

        # payload = {
        #     "amount": amount,
        #     "currency": currency,
        #     ...
        # }

        log.info("Processing payment in payment gateway: %r", payment_id)
        await asyncio.sleep(random.uniform(2, 5))

        new_status = (
            PaymentStatus.SUCCEEDED if random.random() < 0.9 else PaymentStatus.FAILED
        )
        payment_external_id = str(uuid7())
        return new_status, payment_external_id
