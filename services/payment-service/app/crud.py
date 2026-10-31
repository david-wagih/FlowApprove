import uuid
from decimal import Decimal

from sqlalchemy.orm import Session

from app import models
from app.models import PaymentStatus


def get_by_claim_id(db: Session, claim_id: uuid.UUID):
    return db.query(models.Payment).filter(models.Payment.claim_id == claim_id).first()


def list_payments(db: Session, status: PaymentStatus | None, employee_id: uuid.UUID | None):
    query = db.query(models.Payment)
    if status:
        query = query.filter(models.Payment.status == status)
    if employee_id:
        query = query.filter(models.Payment.employee_id == employee_id)
    return query.order_by(models.Payment.created_at.desc()).all()


def create_payment(db: Session, payload: dict):
    payment = models.Payment(
        claim_id=uuid.UUID(payload["claim_id"]),
        employee_id=uuid.UUID(payload["employee_id"]),
        employee_email=payload["employee_email"],
        employee_name=payload["employee_name"],
        amount=Decimal(payload["amount"]),
        currency=payload["currency"],
    )
    db.add(payment)
    db.commit()
    db.refresh(payment)
    return payment


def save(db: Session, payment: models.Payment):
    db.commit()
    db.refresh(payment)
    return payment
