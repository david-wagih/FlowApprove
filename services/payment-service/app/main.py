import logging

from fastapi import FastAPI

from app import events, messaging
from app.database import Base, engine
from app.routers import payments

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Payment Service", version="0.1.0")

app.include_router(payments.router)


@app.on_event("startup")
def startup():
    messaging.start_consumer(
        queue_name="payment_service.expense_approved",
        routing_key="expense.approved",
        on_message=events.handle_expense_approved,
    )


@app.get("/health")
def health():
    return {"status": "ok", "service": "payment-service"}
