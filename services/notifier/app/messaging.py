import json
import logging
import time

import pika

from app.config import settings

logger = logging.getLogger("messaging")

EXCHANGE = "expenses_exchange"


def _connect():
    return pika.BlockingConnection(pika.URLParameters(settings.RABBITMQ_URL))


def run_consumer(queue_name: str, routing_keys: list[str], on_message) -> None:
    """Blocking pika consumer loop over one queue bound to several routing keys, retrying if the broker
    isn't up yet. This is the notifier's main loop."""
    while True:
        try:
            connection = _connect()
            channel = connection.channel()
            channel.exchange_declare(exchange=EXCHANGE, exchange_type="topic", durable=True)
            channel.queue_declare(queue=queue_name, durable=True)
            for routing_key in routing_keys:
                channel.queue_bind(exchange=EXCHANGE, queue=queue_name, routing_key=routing_key)

            def _callback(ch, method, properties, body):
                try:
                    on_message(method.routing_key, json.loads(body))
                    ch.basic_ack(delivery_tag=method.delivery_tag)
                except Exception:
                    logger.exception("Failed to process message on %s", method.routing_key)
                    ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

            channel.basic_qos(prefetch_count=1)
            channel.basic_consume(queue=queue_name, on_message_callback=_callback)
            logger.info("notifier consuming %s -> queue %s", ", ".join(routing_keys), queue_name)
            channel.start_consuming()
        except pika.exceptions.AMQPConnectionError:
            logger.warning("RabbitMQ not reachable yet, retrying in 5s...")
            time.sleep(5)
