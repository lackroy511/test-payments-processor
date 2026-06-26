from src.payments_publisher.repositories.payments import PublisherUnitOfWork
from src.payments_publisher.services.payments import PublisherService
import asyncio
import logging
from faststream import FastStream, Context
from faststream.rabbit import RabbitBroker

from src.core.config.settings import settings
from src.core.db.base import get_db_sessionmaker

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

broker = RabbitBroker(settings.rabbit_url)
app = FastStream(broker)

keep_running = True


async def outbox_worker(broker: RabbitBroker) -> None:
    sessionmaker = await get_db_sessionmaker()
    uow = PublisherUnitOfWork(sessionmaker=sessionmaker)
    service = PublisherService(uow=uow, broker=broker)

    log.info("Starting Outbox Poller...")

    while keep_running:
        try:
            processed = await service.process_outbox_messages()
        except Exception as e:
            log.error("Error in outbox worker: %s", e)

        if processed is None:
            await asyncio.sleep(1.0)


@app.on_startup
async def setup_publisher(broker: RabbitBroker = Context()) -> None:
    asyncio.create_task(outbox_worker(broker))


@app.on_shutdown
async def shutdown_publisher() -> None:
    global keep_running
    keep_running = False
    log.info("Shutting down Outbox Poller...")
