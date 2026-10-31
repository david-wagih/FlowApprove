import logging

from app import messaging, processor
from app.templates import TEMPLATES

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")


def main():
    messaging.run_consumer(
        queue_name="notifier.all_events",
        routing_keys=list(TEMPLATES),
        on_message=processor.send_notification,
    )


if __name__ == "__main__":
    main()
