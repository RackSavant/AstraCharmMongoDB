import math
import time
import uuid
from typing import Dict, List, Optional

from app import llm
from app.db import get_db, using_atlas
from app.logger import log_decision

ALLOWED_PREFERENCES = {
    "size": {"compact", "bold"},
    "pattern": {"smooth", "grooved"},
    "motif": {"moon", "star", "heart"},
}
MIN_PROMOTE_CONFIDENCE = 0.5
INITIAL_CONFIDENCE = 0.6
REINFORCE_STEP = 0.2

EXTRACT_SYSTEM = (
    "Extract at most one durable customer preference from a design rejection reason. "
    "Return JSON {key, value, rule} where key is one of size|pattern|motif, or {} if none."
)


def _cos(a: List[float], b: List[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a)) or 1.0
    nb = math.sqrt(sum(y * y for y in b)) or 1.0
    return dot / (na * nb)


def record_episode(customer_id: str, design_id: str, verdict: str, reason_text: str, spec: dict) -> str:
    episode = {
        "id": uuid.uuid4().hex,
        "customer_id": customer_id,
        "design_id": design_id,
        "type": "episodic",
        "verdict": verdict,
        "reason_text": reason_text,
        "spec_snapshot": spec,
        "embedding": llm.embed(reason_text) if reason_text else None,
        "ts": time.time(),
    }
    get_db().feedback.insert_one(dict(episode))
    log_decision(customer_id, "episode_recorded", design_id, memory_type="episodic",
                 episode_id=episode["id"], verdict=verdict, reason_text=reason_text)
    return episode["id"]


def extract_candidate(customer_id: str, reason_text: str, design_id: str) -> Optional[dict]:
    raw = llm.complete_json("extract_preference", EXTRACT_SYSTEM, reason_text, {"reason_text": reason_text})
    if not raw or "key" not in raw or "value" not in raw:
        log_decision(customer_id, "memory_candidate_none", design_id, reason_text=reason_text)
        return None
    cand = {"key": raw["key"], "value": raw["value"], "rule": raw.get("rule", ""),
            "confidence": INITIAL_CONFIDENCE, "scope": "customer"}
    log_decision(customer_id, "memory_candidate_extracted", design_id, candidate=cand)
    return cand


def evaluate_candidate(cand: dict) -> Dict:
    if cand["key"] not in ALLOWED_PREFERENCES or cand["value"] not in ALLOWED_PREFERENCES[cand["key"]]:
        return {"ok": False, "reason": "not in memory whitelist"}
    if cand["confidence"] < MIN_PROMOTE_CONFIDENCE:
        return {"ok": False, "reason": "confidence below promotion threshold"}
    if cand.get("scope") != "customer":
        return {"ok": False, "reason": "unsupported scope"}
    return {"ok": True, "reason": "passed relevance, confidence and scope checks"}


def promote(customer_id: str, cand: dict, evidence_id: str, design_id: Optional[str] = None) -> dict:
    db = get_db()
    now = time.time()
    same = db.memories.find_one({"customer_id": customer_id, "key": cand["key"], "value": cand["value"]})
    if same:
        conf = min(1.0, same["confidence"] + REINFORCE_STEP)
        db.memories.update_one({"id": same["id"]}, {"$set": {"confidence": conf, "updated_ts": now},
                                                    "$push": {"evidence_ids": evidence_id}})
        mem_id = same["id"]
    else:
        for old in list(db.memories.find({"customer_id": customer_id, "key": cand["key"]})):
            db.memories.delete_one({"id": old["id"]})
            log_decision(customer_id, "memory_superseded", design_id, memory_id=old["id"],
                         old_value=old["value"], new_value=cand["value"])
        mem_id = uuid.uuid4().hex
        db.memories.insert_one({
            "id": mem_id, "customer_id": customer_id, "type": "semantic", "status": "promoted",
            "key": cand["key"], "value": cand["value"], "rule": cand["rule"],
            "confidence": cand["confidence"], "scope": "customer", "evidence_ids": [evidence_id],
            "created_ts": now, "updated_ts": now,
        })
    log_decision(customer_id, "memory_promoted", design_id, memory_id=mem_id, key=cand["key"],
                 value=cand["value"], rule=cand["rule"], evidence_id=evidence_id)
    return db.memories.find_one({"id": mem_id}, {"_id": 0})


def learn_from_rejection(customer_id: str, design_id: str, reason_text: str, evidence_id: str) -> Optional[dict]:
    cand = extract_candidate(customer_id, reason_text, design_id)
    if not cand:
        return None
    verdict = evaluate_candidate(cand)
    log_decision(customer_id, "memory_candidate_evaluated", design_id, candidate=cand, **verdict)
    if not verdict["ok"]:
        return None
    return promote(customer_id, cand, evidence_id, design_id)


def list_memories(customer_id: str) -> List[dict]:
    return list(get_db().memories.find({"customer_id": customer_id, "status": "promoted"}, {"_id": 0}))


def delete_memory(customer_id: str, memory_id: str) -> bool:
    res = get_db().memories.delete_one({"customer_id": customer_id, "id": memory_id})
    if res.deleted_count:
        log_decision(customer_id, "memory_deleted", None, memory_id=memory_id, actor="customer")
    return bool(res.deleted_count)


def _similar_episodes(customer_id: str, query: str, limit: int = 3) -> List[dict]:
    qv = llm.embed(query)
    if using_atlas():
        try:
            pipeline = [
                {"$vectorSearch": {"index": "feedback_vec", "path": "embedding", "queryVector": qv,
                                   "numCandidates": 50, "limit": limit, "filter": {"customer_id": customer_id}}},
                {"$project": {"_id": 0, "embedding": 0}},
            ]
            return list(get_db().feedback.aggregate(pipeline))
        except Exception as exc:
            log_decision(customer_id, "vector_search_fallback", None, error=str(exc))
    docs = list(get_db().feedback.find({"customer_id": customer_id, "embedding": {"$ne": None}}, {"_id": 0}))
    docs.sort(key=lambda d: _cos(qv, d["embedding"]), reverse=True)
    return [{k: v for k, v in d.items() if k != "embedding"} for d in docs[:limit]]


def recall(customer_id: str, query: str) -> Dict:
    return {"preferences": list_memories(customer_id),
            "similar_episodes": _similar_episodes(customer_id, query)}
