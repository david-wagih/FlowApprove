import json
from datetime import datetime

import redis

from app.config import settings

# approval-service keeps its state in Redis only:
#   approval:<claim_id>  -> JSON of the claim + decision (status PENDING / APPROVED / REJECTED)
#   inbox:<manager_id>   -> sorted set of pending claim ids, scored by submission time (oldest first)
redis_client = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)


def _approval_key(claim_id: str) -> str:
    return f"approval:{claim_id}"


def _inbox_key(manager_id: str) -> str:
    return f"inbox:{manager_id}"


def add_pending(claim: dict) -> bool:
    """Stores a newly submitted claim. Returns False if we've already seen it (a redelivered event)."""
    record = {**claim, "status": "PENDING", "decided_by": None, "decided_at": None, "reason": None}
    if not redis_client.set(_approval_key(claim["claim_id"]), json.dumps(record), nx=True):
        return False
    submitted_at = datetime.fromisoformat(claim["submitted_at"]).timestamp()
    redis_client.zadd(_inbox_key(claim["manager_id"]), {claim["claim_id"]: submitted_at})
    return True


def get_approval(claim_id: str) -> dict | None:
    raw = redis_client.get(_approval_key(claim_id))
    return json.loads(raw) if raw else None


def list_inbox(manager_id: str) -> list[dict]:
    claim_ids = redis_client.zrange(_inbox_key(manager_id), 0, -1)
    if not claim_ids:
        return []
    raws = redis_client.mget([_approval_key(c) for c in claim_ids])
    return [json.loads(raw) for raw in raws if raw]


def record_decision(record: dict, status: str, manager_id: str, reason: str | None) -> dict:
    record = {
        **record,
        "status": status,
        "decided_by": manager_id,
        "decided_at": datetime.utcnow().isoformat(),
        "reason": reason,
    }
    pipe = redis_client.pipeline()
    pipe.set(_approval_key(record["claim_id"]), json.dumps(record))
    pipe.zrem(_inbox_key(record["manager_id"]), record["claim_id"])
    pipe.execute()
    return record
