import asyncio
import logging
import random
from uuid import UUID

import httpx
from sqlalchemy.exc import DBAPIError, OperationalError

from src.core.db.models import PaymentStatus
from src.core.utils.backoff import Backoff
from src.payments_consumer.repositories.payments import ConsumerUnitOfWork

log = logging.getLogger(__name__)


class ConsumerService:
    def __init__(self, uow: ConsumerUnitOfWork) -> None:
        self._uow = uow

    @Backoff(
        exceptions=(
            OperationalError,
            DBAPIError,
            httpx.HTTPError,
        ),
    )
    async def process_payment(self, payment_id: UUID) -> None:
        async with self._uow as uow:
            payment = await uow.payment_repo.get_by_id(payment_id)

            if payment is None:
                log.warning("Payment %s not found, skipping", payment_id)
                return

            if payment.status == PaymentStatus.PENDING:
                await asyncio.sleep(random.uniform(2, 5))

                success = random.random() < 0.9
                new_status = (
                    PaymentStatus.SUCCEEDED if success else PaymentStatus.FAILED
                )

                await uow.payment_repo.update_status(payment_id, new_status)
                await uow.commit()

                payment.status = new_status

            await self._send_webhook(payment.webhook_url, payment_id, payment.status)

    async def _send_webhook(
        self,
        url: str,
        payment_id: UUID,
        status: PaymentStatus,
    ) -> None:
        log.info(
            "Sending webhook to %s for payment %s with status %s",
            url,
            payment_id,
            status,
        )
        # async with httpx.AsyncClient() as client:
        #     response = await client.post(
        #         url,
        #         json={
        #             "payment_id": str(payment_id),
        #             "status": status.value,
        #         },
        #         timeout=30.0,
        #     )
        #     response.raise_for_status()
