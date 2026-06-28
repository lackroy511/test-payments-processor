import asyncio
import logging
from uuid import UUID

from faststream import AckPolicy, FastStream
from faststream.rabbit import RabbitBroker, RabbitMessage

from src.core.broker.rabbitmq import dlq_queue, payments_exchange, payments_new_queue
from src.core.config.settings import settings
from src.core.db.base import get_db_sessionmaker
from src.payments_consumer.repositories.payments import ConsumerUnitOfWork
from src.payments_consumer.services.payments import ConsumerService
from src.payments_consumer.services.webhook_sender import WebhookSender

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

broker = RabbitBroker(settings.rabbit_url)

app = FastStream(broker)

webhook_worker: asyncio.Task | None = None


@broker.subscriber(
    queue=payments_new_queue,
    exchange=payments_exchange,
    ack_policy=AckPolicy.MANUAL,
)
async def handle_payment_created(body: dict, msg: RabbitMessage) -> None:
    payment_id_raw = body.get("payment_id")

    if not payment_id_raw:
        log.warning("Message without payment_id: %s", body)
        await msg.nack(requeue=False)
        return

    payment_id = UUID(payment_id_raw)

    sessionmaker = await get_db_sessionmaker()
    uow = ConsumerUnitOfWork(sessionmaker=sessionmaker)
    service = ConsumerService(uow=uow)

    try:
        await service.process_payment(payment_id)
        log.info("Payment %s processed successfully", payment_id)
        await msg.ack()
    except Exception:
        log.exception("Payment %s failed, sending to DLQ", payment_id)
        await msg.nack(requeue=False)


@app.on_startup
async def setup() -> None:
    global webhook_worker

    await broker.connect()
    await broker.declare_queue(dlq_queue)

    sessionmaker = await get_db_sessionmaker()
    webhook_uow = ConsumerUnitOfWork(sessionmaker=sessionmaker)
    webhook_sender = WebhookSender(uow=webhook_uow)
    webhook_worker = asyncio.create_task(webhook_sender.run())


@app.on_shutdown
async def shutdown() -> None:
    global webhook_worker

    if webhook_worker is not None:
        webhook_worker.cancel()
        try:
            await webhook_worker
        except asyncio.CancelledError:
            pass


if __name__ == "__main__":
    asyncio.run(app.run())
