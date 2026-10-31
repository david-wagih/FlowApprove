from dataclasses import dataclass

from fastapi import Header, HTTPException
from jose import jwt

from app.config import settings


@dataclass
class Caller:
    id: str
    role: str
    name: str


def get_current_manager(authorization: str = Header(...)) -> Caller:
    """Verifies the JWT issued by employee-service locally, with the shared secret — no network call.
    Fast and keeps working if employee-service is down, but both services must share JWT_SECRET."""
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")
    token = authorization.removeprefix("Bearer ").strip()
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    caller = Caller(id=payload["sub"], role=payload.get("role", ""), name=payload.get("name", ""))
    if caller.role != "MANAGER":
        raise HTTPException(status_code=403, detail="Only managers can use the approval workflow")
    return caller
