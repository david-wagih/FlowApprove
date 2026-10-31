import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict

from app.models import PaymentStatus


class PaymentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    claim_id: uuid.UUID
    employee_id: uuid.UUID
    employee_email: str
    amount: Decimal
    currency: str
    status: PaymentStatus
    attempts: int
    failure_reason: str | None
    reference: str | None
    created_at: datetime
    updated_at: datetime
