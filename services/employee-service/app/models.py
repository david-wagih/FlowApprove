import enum
import uuid
from datetime import datetime

from sqlalchemy import Column, Date, DateTime, Enum, Numeric, String
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base


class Role(str, enum.Enum):
    EMPLOYEE = "EMPLOYEE"
    MANAGER = "MANAGER"


class ClaimStatus(str, enum.Enum):
    SUBMITTED = "SUBMITTED"  # waiting on the manager (approval-service)
    APPROVED = "APPROVED"  # approved, payment in progress (payment-service)
    REJECTED = "REJECTED"  # rejected by the manager
    PAID = "PAID"  # reimbursement went through
    PAYMENT_FAILED = "PAYMENT_FAILED"  # reimbursement failed, can be retried on payment-service


class ClaimCategory(str, enum.Enum):
    TRAVEL = "TRAVEL"
    LODGING = "LODGING"
    MEALS = "MEALS"
    SOFTWARE = "SOFTWARE"
    OFFICE_SUPPLIES = "OFFICE_SUPPLIES"
    OTHER = "OTHER"


class Employee(Base):
    __tablename__ = "employees"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=False)
    role = Column(Enum(Role), nullable=False, default=Role.EMPLOYEE)
    # Who approves this employee's claims. Must point at a MANAGER.
    manager_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class Claim(Base):
    __tablename__ = "claims"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    employee_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    manager_id = Column(UUID(as_uuid=True), nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    currency = Column(String(3), nullable=False)
    category = Column(Enum(ClaimCategory), nullable=False)
    description = Column(String, nullable=False)
    expense_date = Column(Date, nullable=False)
    status = Column(Enum(ClaimStatus), nullable=False, default=ClaimStatus.SUBMITTED)
    # Last reason the claim didn't go through (manager's rejection or payment failure).
    status_reason = Column(String, nullable=True)
    payment_reference = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
