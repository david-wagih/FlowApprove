import uuid

from fastapi import Depends, Header, HTTPException
from sqlalchemy.orm import Session

from app import crud, security
from app.database import get_db


def get_current_employee(authorization: str = Header(...), db: Session = Depends(get_db)):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")
    token = authorization.removeprefix("Bearer ").strip()
    try:
        employee_id = security.decode_access_token(token)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    employee = crud.get_employee_by_id(db, uuid.UUID(employee_id))
    if not employee:
        raise HTTPException(status_code=401, detail="Employee not found")
    return employee
