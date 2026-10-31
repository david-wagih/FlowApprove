from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import crud, models, schemas, security
from app.database import get_db

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=schemas.EmployeeOut, status_code=status.HTTP_201_CREATED)
def register(payload: schemas.EmployeeCreate, db: Session = Depends(get_db)):
    if crud.get_employee_by_email(db, payload.email):
        raise HTTPException(status_code=409, detail="Email already registered")
    if payload.manager_id:
        manager = crud.get_employee_by_id(db, payload.manager_id)
        if not manager or manager.role != models.Role.MANAGER:
            raise HTTPException(status_code=422, detail="manager_id must reference an existing MANAGER")
    return crud.create_employee(db, payload)


@router.post("/login", response_model=schemas.TokenResponse)
def login(payload: schemas.LoginRequest, db: Session = Depends(get_db)):
    employee = crud.get_employee_by_email(db, payload.email)
    if not employee or not security.verify_password(payload.password, employee.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return schemas.TokenResponse(access_token=security.create_access_token(employee))
