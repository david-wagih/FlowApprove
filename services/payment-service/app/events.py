import logging
import uuid

from app import crud, processor
from app.database import SessionLocal

logger = logging.getLogger("events")


def handle_expense_approved(payload: dict) -> None:
    """Reacts to `expense.approved` by reimbursing the employee."""
    db = SessionLocal()
    try:
        if crud.get_by_claim_id(db, uuid.UUID(payload["claim_id"])):
            # RabbitMQ delivers at-least-once, so the same event can show up twice — make that harmless.
            logger.info("Claim %s already has a payment, skipping duplicate", payload["claim_id"])
            return
        processor.process(db, crud.create_payment(db, payload))
    finally:
        db.close()
