import asyncio
import logging
from datetime import datetime, timedelta, timezone
from uuid import UUID

import httpx

from src.core.db.models import PaymentStatus
from src.core.utils.backoff import Backoff
from src.payments_consumer.repositories.payments import ConsumerUnitOfWork

log = logging.getLogger(__name__)


class WebhookSender:
    def __init__(self, uow: ConsumerUnitOfWork) -> None:
        self._uow = uow

    async def run(self) -> None:
        while True:
            async with self._uow as uow:
                try:
                    processed_after = datetime.now(timezone.utc) - timedelta(days=1)
                    success_payments = (
                        await uow.payment_repo.get_processed_payments_for_webhook(
                            is_webhook_sent=False,
                            processed_after=processed_after,
                        )
                    )
                    for payment in success_payments:
                        await self._send_webhook(
                            payment.webhook_url,
                            payment.id,
                            payment.status,
                        )
                        await uow.payment_repo.update_payment(
                            payment.id,
                            is_webhook_sent=True,
                        )
                        await uow.commit()
                    
                    if len(success_payments) == 0:
                        await asyncio.sleep(1)

                except Exception:
                    log.exception("Error while sending webhooks: ")

    @Backoff(exceptions=(httpx.HTTPError,))
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
        await asyncio.sleep(0.1)
