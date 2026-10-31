import json
import logging
import threading
import time

import pika

from app.config import settings

logger = logging.getLogger("messaging")

EXCHANGE = "expenses_exchange"


def _connect():
    return pika.BlockingConnection(pika.URLParameters(settings.RABBITMQ_URL))


def publish_event(routing_key: str, payload: dict) -> None:
    connection = _connect()
    try:
        channel = connection.channel()
        channel.exchange_declare(exchange=EXCHANGE, exchange_type="topic", durable=True)
        channel.basic_publish(
            exchange=EXCHANGE,
            routing_key=routing_key,
            body=json.dumps(payload, default=str),
            properties=pika.BasicProperties(content_type="application/json", delivery_mode=2),
        )
    finally:
        connection.close()


def start_consumer(queue_name: str, routing_key: str, on_message) -> None:
    """Runs a blocking pika consumer loop in a background thread, retrying if the broker isn't up yet."""

    def _run():
        while True:
            try:
                connection = _connect()
                channel = connection.channel()
                channel.exchange_declare(exchange=EXCHANGE, exchange_type="topic", durable=True)
                channel.queue_declare(queue=queue_name, durable=True)
                channel.queue_bind(exchange=EXCHANGE, queue=queue_name, routing_key=routing_key)

                def _callback(ch, method, properties, body):
                    try:
                        on_message(json.loads(body))
                        ch.basic_ack(delivery_tag=method.delivery_tag)
                    except Exception:
                        logger.exception("Failed to process message on %s", routing_key)
                        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

                channel.basic_qos(prefetch_count=1)
                channel.basic_consume(queue=queue_name, on_message_callback=_callback)
                logger.info("Consuming %s -> queue %s", routing_key, queue_name)
                channel.start_consuming()
            except pika.exceptions.AMQPConnectionError:
                logger.warning("RabbitMQ not reachable yet, retrying in 5s...")
                time.sleep(5)

    thread = threading.Thread(target=_run, daemon=True)
    thread.start()
