import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import crud, processor, schemas
from app.database import get_db
from app.models import PaymentStatus

router = APIRouter(prefix="/payments", tags=["payments"])


@router.get("", response_model=list[schemas.PaymentOut])
def list_payments(
    status: PaymentStatus | None = None,
    employee_id: uuid.UUID | None = None,
    db: Session = Depends(get_db),
):
    return crud.list_payments(db, status, employee_id)


@router.get("/{claim_id}", response_model=schemas.PaymentOut)
def read_payment(claim_id: uuid.UUID, db: Session = Depends(get_db)):
    payment = crud.get_by_claim_id(db, claim_id)
    if not payment:
        raise HTTPException(status_code=404, detail="No payment for this claim")
    return payment


@router.post("/{claim_id}/retry", response_model=schemas.PaymentOut)
def retry_payment(claim_id: uuid.UUID, db: Session = Depends(get_db)):
    """Finance retries a FAILED payment (e.g. after the bank timeout clears)."""
    payment = crud.get_by_claim_id(db, claim_id)
    if not payment:
        raise HTTPException(status_code=404, detail="No payment for this claim")
    if payment.status != PaymentStatus.FAILED:
        raise HTTPException(status_code=409, detail=f"Payment is {payment.status.value}, only FAILED can be retried")
    return processor.process(db, payment)
