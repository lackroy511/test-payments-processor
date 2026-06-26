from src.core.db.models import OutboxMessageType
from src.core.broker.rabbitmq import payments_exchange, dlq_queue, payments_new_queue
import asyncio
import logging

from faststream import FastStream
from faststream.rabbit import RabbitBroker

from src.core.config.settings import settings
from src.core.db.base import get_db_sessionmaker
from src.payments_publisher.repositories.payments import PublisherUnitOfWork
from src.payments_publisher.services.payments import PublisherService

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

broker = RabbitBroker(settings.rabbit_url)

app = FastStream(broker)

keep_running = True


async def outbox_worker(broker: RabbitBroker) -> None:
    await broker.connect()
    exchange = await broker.declare_exchange(payments_exchange)
    await broker.declare_queue(dlq_queue)
    queue = await broker.declare_queue(payments_new_queue)
    await queue.bind(
        exchange=exchange,
        routing_key=OutboxMessageType.PAYMENT_CREATED.value,
    )

    sessionmaker = await get_db_sessionmaker()
    uow = PublisherUnitOfWork(sessionmaker=sessionmaker)
    service = PublisherService(uow=uow, broker=broker)

    log.info("Starting Outbox Poller...")

    while keep_running:
        processed_count = None
        try:
            processed_count = await service.process_outbox_messages()
        except Exception as e:
            log.error("Error in outbox worker: %s", e)

        if processed_count is None:
            await asyncio.sleep(1.0)


@app.on_startup
async def setup_publisher() -> None:
    asyncio.create_task(outbox_worker(broker))


@app.on_shutdown
async def shutdown_publisher() -> None:
    global keep_running
    keep_running = False
    log.info("Shutting down Outbox Poller...")


if __name__ == "__main__":
    asyncio.run(app.run())
