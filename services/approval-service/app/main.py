import logging

from fastapi import FastAPI

from app import events, messaging
from app.routers import approvals

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

app = FastAPI(title="Approval Service", version="0.1.0")

app.include_router(approvals.router)


@app.on_event("startup")
def startup():
    messaging.start_consumer(
        queue_name="approval_service.expense_submitted",
        routing_key="expense.submitted",
        on_message=events.handle_expense_submitted,
    )


@app.get("/health")
def health():
    return {"status": "ok", "service": "approval-service"}
