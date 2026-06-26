import asyncio
import logging

from faststream import FastStream
from faststream.rabbit import RabbitBroker

from src.core.broker.rabbitmq import dlq_queue, payments_exchange, payments_new_queue
from src.core.config.settings import settings
from src.core.db.base import get_db_sessionmaker
from src.core.db.models import OutboxMessageType
from src.payments_publisher.repositories.payments import PublisherUnitOfWork
from src.payments_publisher.services.payments import PublisherService

log = logging.getLogger(__name__)

broker = RabbitBroker(settings.rabbit_url)

app = FastStream(broker)

shutdown_event = asyncio.Event()
worker_task: asyncio.Task | None = None


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

    while not shutdown_event.is_set():
        try:
            processed_count = await service.process_outbox_messages()
        except Exception as e:
            log.error("Error in outbox worker: %s", e)
            await asyncio.sleep(1.0)
            continue

        if processed_count == 0:
            await asyncio.sleep(1.0)


@app.on_startup
async def setup_publisher() -> None:
    global worker_task
    worker_task = asyncio.create_task(outbox_worker(broker))


@app.on_shutdown
async def shutdown_publisher() -> None:
    log.info("Shutting down Outbox Poller...")
    shutdown_event.set()
    if worker_task is not None:
        try:
            await asyncio.wait_for(worker_task, timeout=30.0)
        except TimeoutError:
            log.warning("Outbox worker did not finish within timeout, cancelling...")
            worker_task.cancel()


if __name__ == "__main__":
    asyncio.run(app.run())
