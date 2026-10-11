import time
import uuid
from typing import Optional

from app.db import get_db


def log_decision(customer_id: str, step: str, design_id: Optional[str] = None, **fields) -> dict:
    entry = {
        "id": uuid.uuid4().hex,
        "customer_id": customer_id,
        "design_id": design_id,
        "step": step,
        "ts": time.time(),
        **fields,
    }
    get_db().agent_events.insert_one(dict(entry))
    return entry


def get_log(design_id: Optional[str] = None, customer_id: Optional[str] = None) -> list:
    q = {}
    if design_id:
        q["design_id"] = design_id
    if customer_id:
        q["customer_id"] = customer_id
    return list(get_db().agent_events.find(q, {"_id": 0}).sort("ts", 1))
