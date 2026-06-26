from src.payments_publisher.repositories.payments import PublisherUnitOfWork
import logging
from faststream.rabbit import RabbitBroker

from src.core.broker.rabbitmq import payments_exchange

log = logging.getLogger(__name__)


class PublisherService:
    def __init__(self, uow: PublisherUnitOfWork, broker: RabbitBroker) -> None:
        self._uow = uow
        self._broker = broker

    async def process_outbox_messages(self, batch_size: int = 100) -> int | None:
        async with self._uow as uow:
            messages = await uow.outbox_repo.get_pending_batch(limit=batch_size)

            if not messages:
                return

            for msg in messages:
                try:
                    await self._broker.publish(
                        message=msg.payload,
                        exchange=payments_exchange,
                        routing_key=msg.event_type.value,
                    )
                    await uow.outbox_repo.mark_as_published(msg.id)
                except Exception as e:
                    log.error("Failed to publish message %s: %s", msg.id, e)
                    raise e

            await uow.commit()
