import logging
import uuid

from app import crud
from app.database import SessionLocal
from app.models import ClaimStatus

logger = logging.getLogger("events")


def handle_expense_approved(payload: dict) -> None:
    _transition(payload["claim_id"], {ClaimStatus.SUBMITTED}, ClaimStatus.APPROVED, status_reason=None)


def handle_expense_rejected(payload: dict) -> None:
    _transition(
        payload["claim_id"], {ClaimStatus.SUBMITTED}, ClaimStatus.REJECTED, status_reason=payload.get("reason")
    )


def handle_payment_completed(payload: dict) -> None:
    # PAYMENT_FAILED is allowed too: a failed payment can be retried on payment-service.
    _transition(
        payload["claim_id"],
        {ClaimStatus.APPROVED, ClaimStatus.PAYMENT_FAILED},
        ClaimStatus.PAID,
        status_reason=None,
        payment_reference=payload.get("reference"),
    )


def handle_payment_failed(payload: dict) -> None:
    _transition(
        payload["claim_id"],
        {ClaimStatus.APPROVED, ClaimStatus.PAYMENT_FAILED},
        ClaimStatus.PAYMENT_FAILED,
        status_reason=payload.get("reason"),
    )


def _transition(claim_id: str, from_statuses: set[ClaimStatus], to_status: ClaimStatus, **fields) -> None:
    db = SessionLocal()
    try:
        claim = crud.transition(db, uuid.UUID(claim_id), from_statuses, to_status, **fields)
        if claim:
            logger.info("Claim %s -> status=%s", claim_id, claim.status)
        else:
            logger.warning("Ignored move to %s for claim %s (not in an expected state)", to_status, claim_id)
    finally:
        db.close()
