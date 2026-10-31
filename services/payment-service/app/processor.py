import logging
import random
import secrets
import time
from datetime import datetime

from sqlalchemy.orm import Session

from app import crud, messaging, models
from app.config import settings
from app.models import PaymentStatus

logger = logging.getLogger("processor")


def _simulate_transfer(payment: models.Payment) -> str | None:
    """Pretends to call the bank. Returns a failure reason, or None if the transfer went through."""
    time.sleep(settings.PAYMENT_SECONDS)
    if payment.amount > settings.PAYMENT_LIMIT:
        return f"amount {payment.amount} {payment.currency} is above the {settings.PAYMENT_LIMIT} payout limit"
    if random.random() < settings.PAYMENT_FAILURE_RATE:
        return "bank transfer timed out"
    return None


def process(db: Session, payment: models.Payment) -> models.Payment:
    """Runs one payment attempt and publishes `payment.completed` or `payment.failed`."""
    payment.status = PaymentStatus.PROCESSING
    payment.attempts += 1
    crud.save(db, payment)
    logger.info("Paying claim %s: %s %s (attempt %d)", payment.claim_id, payment.amount, payment.currency, payment.attempts)

    reason = _simulate_transfer(payment)
    event = {
        "claim_id": str(payment.claim_id),
        "payment_id": str(payment.id),
        "employee_id": str(payment.employee_id),
        "employee_email": payment.employee_email,
        "employee_name": payment.employee_name,
        "amount": str(payment.amount),
        "currency": payment.currency,
    }

    if reason:
        payment.status = PaymentStatus.FAILED
        payment.failure_reason = reason
        crud.save(db, payment)
        logger.info("Payment for claim %s failed: %s", payment.claim_id, reason)
        messaging.publish_event("payment.failed", event | {"reason": reason, "attempts": payment.attempts})
        return payment

    payment.status = PaymentStatus.COMPLETED
    payment.failure_reason = None
    payment.reference = f"TRX-{secrets.token_hex(4).upper()}"
    crud.save(db, payment)
    logger.info("Payment for claim %s completed (%s)", payment.claim_id, payment.reference)
    messaging.publish_event(
        "payment.completed",
        event | {"reference": payment.reference, "paid_at": datetime.utcnow().isoformat()},
    )
    return payment
