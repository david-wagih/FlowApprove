from fastapi import APIRouter, Depends, HTTPException

from app import messaging, schemas, store
from app.security import Caller, get_current_manager

router = APIRouter(prefix="/approvals", tags=["approvals"])


def _load_for_manager(claim_id: str, manager: Caller) -> dict:
    record = store.get_approval(claim_id)
    # 404 rather than 403 for someone else's report, so managers can't probe other teams' claim ids.
    if not record or record["manager_id"] != manager.id:
        raise HTTPException(status_code=404, detail="Claim not found")
    return record


def _require_pending(record: dict) -> None:
    if record["status"] != "PENDING":
        raise HTTPException(status_code=409, detail=f"Claim was already {record['status']}")


def _event_payload(record: dict) -> dict:
    keys = ("claim_id", "employee_id", "employee_email", "employee_name", "amount", "currency")
    return {k: record[k] for k in keys} | {"decided_at": record["decided_at"]}


@router.get("/inbox", response_model=list[schemas.Approval])
def inbox(manager: Caller = Depends(get_current_manager)):
    """Every claim waiting on the calling manager's decision, oldest first."""
    return store.list_inbox(manager.id)


@router.get("/{claim_id}", response_model=schemas.Approval)
def read_approval(claim_id: str, manager: Caller = Depends(get_current_manager)):
    return _load_for_manager(claim_id, manager)


@router.post("/{claim_id}/approve", response_model=schemas.Approval)
def approve(claim_id: str, manager: Caller = Depends(get_current_manager)):
    record = _load_for_manager(claim_id, manager)
    _require_pending(record)
    record = store.record_decision(record, "APPROVED", manager.id, reason=None)
    messaging.publish_event("expense.approved", _event_payload(record) | {"approved_by": manager.id})
    return record


@router.post("/{claim_id}/reject", response_model=schemas.Approval)
def reject(claim_id: str, payload: schemas.RejectRequest, manager: Caller = Depends(get_current_manager)):
    record = _load_for_manager(claim_id, manager)
    _require_pending(record)
    record = store.record_decision(record, "REJECTED", manager.id, reason=payload.reason)
    messaging.publish_event(
        "expense.rejected",
        _event_payload(record) | {"rejected_by": manager.id, "reason": payload.reason},
    )
    return record
