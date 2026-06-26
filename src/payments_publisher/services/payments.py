import logging

from aiormq import AMQPConnectionError, ConnectionClosed
from faststream.rabbit import RabbitBroker
from sqlalchemy.exc import DBAPIError, OperationalError

from src.core.broker.rabbitmq import payments_exchange
from src.core.utils.backoff import Backoff
from src.payments_publisher.repositories.payments import PublisherUnitOfWork

log = logging.getLogger(__name__)


class PublisherService:
    def __init__(self, uow: PublisherUnitOfWork, broker: RabbitBroker) -> None:
        self._uow = uow
        self._broker = broker

    @Backoff(
        exceptions=(
            OperationalError,
            DBAPIError,
            AMQPConnectionError,
            ConnectionClosed,
        ),
    )
    async def process_outbox_messages(self, batch_size: int = 100) -> int:
        async with self._uow as uow:
            messages = await uow.outbox_repo.get_pending_batch(limit=batch_size)

            if not messages:
                return 0

            processed = 0
            for msg in messages:
                try:
                    await self._broker.publish(
                        message=msg.payload,
                        exchange=payments_exchange,
                        routing_key=msg.event_type.value,
                    )
                    await uow.outbox_repo.mark_as_published(msg.id)
                    processed += 1
                except Exception:
                    log.exception("Failed to publish message %s:", msg.id)

            if processed > 0:
                await uow.commit()

            return processed
