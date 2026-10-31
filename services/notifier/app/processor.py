import logging

from app.config import settings
from app.templates import TEMPLATES

logger = logging.getLogger("notifier")


def send_notification(routing_key: str, payload: dict) -> None:
    """Simulates emailing the employee. A real version would call SES/SendGrid here instead of logging."""
    subject, body = TEMPLATES[routing_key]
    logger.info(
        "EMAIL from=%s to=%s subject=%r body=%r",
        settings.FROM_ADDRESS,
        payload["employee_email"],
        subject,
        body.format(**payload),
    )
