import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import crud, schemas
from app.database import get_db
from app.dependencies import get_current_employee

router = APIRouter(prefix="/employees", tags=["employees"])


@router.get("/me", response_model=schemas.EmployeeOut)
def read_me(current=Depends(get_current_employee)):
    return current


@router.get("/{employee_id}", response_model=schemas.EmployeeOut)
def read_employee(employee_id: uuid.UUID, db: Session = Depends(get_db)):
    employee = crud.get_employee_by_id(db, employee_id)
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    return employee
