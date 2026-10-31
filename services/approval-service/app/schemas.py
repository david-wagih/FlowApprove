from pydantic import BaseModel, Field


class Approval(BaseModel):
    claim_id: str
    employee_id: str
    employee_email: str
    employee_name: str
    manager_id: str
    amount: str
    currency: str
    category: str
    description: str
    submitted_at: str
    status: str
    decided_by: str | None
    decided_at: str | None
    reason: str | None


class RejectRequest(BaseModel):
    reason: str = Field(min_length=1, max_length=500)
