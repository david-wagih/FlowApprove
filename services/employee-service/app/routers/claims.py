import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import crud, messaging, schemas
from app.database import get_db
from app.dependencies import get_current_employee

router = APIRouter(prefix="/claims", tags=["claims"])


@router.post("", response_model=schemas.ClaimOut, status_code=201)
def submit_claim(
    payload: schemas.ClaimCreate,
    current=Depends(get_current_employee),
    db: Session = Depends(get_db),
):
    if not current.manager_id:
        raise HTTPException(status_code=422, detail="You have no manager assigned, nobody can approve this")

    claim = crud.create_claim(db, current, payload)

    # Everything downstream (approval, payment, notifications) needs who and how much, so the event
    # carries it — no other service has to call back here to find out.
    messaging.publish_event(
        "expense.submitted",
        {
            "claim_id": str(claim.id),
            "employee_id": str(current.id),
            "employee_email": current.email,
            "employee_name": current.full_name,
            "manager_id": str(claim.manager_id),
            "amount": str(claim.amount),
            "currency": claim.currency,
            "category": claim.category.value,
            "description": claim.description,
            "submitted_at": datetime.utcnow().isoformat(),
        },
    )

    return claim


@router.get("", response_model=list[schemas.ClaimOut])
def list_my_claims(current=Depends(get_current_employee), db: Session = Depends(get_db)):
    return crud.list_claims_for_employee(db, current.id)


@router.get("/{claim_id}", response_model=schemas.ClaimOut)
def read_claim(claim_id: uuid.UUID, current=Depends(get_current_employee), db: Session = Depends(get_db)):
    claim = crud.get_claim(db, claim_id)
    if not claim or claim.employee_id != current.id:
        raise HTTPException(status_code=404, detail="Claim not found")
    return claim
