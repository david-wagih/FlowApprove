import logging

from app import store

logger = logging.getLogger("events")


def handle_expense_submitted(payload: dict) -> None:
    """Reacts to `expense.submitted` by putting the claim in the manager's approval inbox."""
    if store.add_pending(payload):
        logger.info("Claim %s waiting on manager %s", payload["claim_id"], payload["manager_id"])
    else:
        logger.info("Claim %s already in the workflow, skipping duplicate", payload["claim_id"])
