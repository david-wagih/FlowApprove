import logging

from fastapi import FastAPI

from app import events, messaging
from app.database import Base, engine
from app.routers import auth, claims, employees

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Employee Service", version="0.1.0")

app.include_router(auth.router)
app.include_router(employees.router)
app.include_router(claims.router)

# Keeps each claim's status in sync with what happens downstream, so employees see it in one place.
_EVENT_HANDLERS = {
    "expense.approved": events.handle_expense_approved,
    "expense.rejected": events.handle_expense_rejected,
    "payment.completed": events.handle_payment_completed,
    "payment.failed": events.handle_payment_failed,
}


@app.on_event("startup")
def startup():
    for routing_key, handler in _EVENT_HANDLERS.items():
        messaging.start_consumer(
            queue_name=f"employee_service.{routing_key.replace('.', '_')}",
            routing_key=routing_key,
            on_message=handler,
        )


@app.get("/health")
def health():
    return {"status": "ok", "service": "employee-service"}
