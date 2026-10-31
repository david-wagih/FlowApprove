import uuid

from sqlalchemy.orm import Session

from app import models, schemas, security


def get_employee_by_email(db: Session, email: str):
    return db.query(models.Employee).filter(models.Employee.email == email).first()


def get_employee_by_id(db: Session, employee_id: uuid.UUID):
    return db.query(models.Employee).filter(models.Employee.id == employee_id).first()


def create_employee(db: Session, payload: schemas.EmployeeCreate):
    employee = models.Employee(
        email=payload.email,
        hashed_password=security.hash_password(payload.password),
        full_name=payload.full_name,
        role=payload.role,
        manager_id=payload.manager_id,
    )
    db.add(employee)
    db.commit()
    db.refresh(employee)
    return employee


def get_claim(db: Session, claim_id: uuid.UUID):
    return db.query(models.Claim).filter(models.Claim.id == claim_id).first()


def list_claims_for_employee(db: Session, employee_id: uuid.UUID):
    return (
        db.query(models.Claim)
        .filter(models.Claim.employee_id == employee_id)
        .order_by(models.Claim.created_at.desc())
        .all()
    )


def create_claim(db: Session, employee: models.Employee, payload: schemas.ClaimCreate):
    claim = models.Claim(
        employee_id=employee.id,
        manager_id=employee.manager_id,
        amount=payload.amount,
        currency=payload.currency,
        category=payload.category,
        description=payload.description,
        expense_date=payload.expense_date,
    )
    db.add(claim)
    db.commit()
    db.refresh(claim)
    return claim


def transition(
    db: Session,
    claim_id: uuid.UUID,
    from_statuses: set[models.ClaimStatus],
    to_status: models.ClaimStatus,
    **fields,
):
    """Moves a claim to a new status, but only from one it's allowed to come from — so a duplicate or
    out-of-order event can't e.g. flip a REJECTED claim to PAID."""
    claim = get_claim(db, claim_id)
    if not claim or claim.status not in from_statuses:
        return None
    claim.status = to_status
    for name, value in fields.items():
        setattr(claim, name, value)
    db.commit()
    db.refresh(claim)
    return claim
