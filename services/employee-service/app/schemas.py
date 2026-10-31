import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models import ClaimCategory, ClaimStatus, Role


class EmployeeCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    role: Role = Role.EMPLOYEE
    manager_id: uuid.UUID | None = None


class EmployeeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: EmailStr
    full_name: str
    role: Role
    manager_id: uuid.UUID | None
    created_at: datetime


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class ClaimCreate(BaseModel):
    amount: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    currency: str = Field(default="EUR", pattern=r"^[A-Z]{3}$")
    category: ClaimCategory
    description: str = Field(min_length=1, max_length=1000)
    expense_date: date


class ClaimOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    employee_id: uuid.UUID
    manager_id: uuid.UUID
    amount: Decimal
    currency: str
    category: ClaimCategory
    description: str
    expense_date: date
    status: ClaimStatus
    status_reason: str | None
    payment_reference: str | None
    created_at: datetime
    updated_at: datetime
