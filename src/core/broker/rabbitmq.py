from faststream.rabbit import RabbitExchange, RabbitQueue

payments_exchange = RabbitExchange("payments_exchange", auto_delete=False)

dlq_queue = RabbitQueue("payments.dlq", auto_delete=False)

payments_new_queue = RabbitQueue(
    "payments.new",
    auto_delete=False,
    routing_key="payment.created",
    arguments={
        "x-dead-letter-exchange": "",
        "x-dead-letter-routing-key": "payments.dlq",
    },
)
