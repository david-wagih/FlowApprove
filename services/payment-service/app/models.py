import enum
import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, Enum, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base


class PaymentStatus(str, enum.Enum):
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class Payment(Base):
    __tablename__ = "payments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # Unique so a redelivered `expense.approved` can never reimburse the same claim twice.
    claim_id = Column(UUID(as_uuid=True), unique=True, nullable=False)
    employee_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    employee_email = Column(String, nullable=False)
    employee_name = Column(String, nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    currency = Column(String(3), nullable=False)
    status = Column(Enum(PaymentStatus), nullable=False, default=PaymentStatus.PROCESSING)
    attempts = Column(Integer, nullable=False, default=0)
    failure_reason = Column(String, nullable=True)
    # The (fake) bank transfer reference, set once the payment completes.
    reference = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
