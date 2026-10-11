import json
import time
import uuid
from typing import Optional

from pydantic import ValidationError

from app import llm, memory
from app.db import get_db
from app.design_spec import RingSpec
from app.logger import log_decision
from app.stl_generator import export_stl
from app.validator import auto_fix, estimate_weight_g, validate

MAX_REVISIONS = 2

DESIGN_SYSTEM = (
    "You are Astra, a jewelry merchandiser. Return ONLY a JSON ring spec with keys: "
    "band_width_mm, band_thickness_mm, inner_diameter_mm, profile(flat|domed|comfort), "
    "stone_shape(none|round|oval), stone_diameter_mm, setting_height_mm, "
    "metal(silver|gold|platinum), style_tags[], rationale. Respect customer preferences and "
    "manufacturing constraints."
)


class AgentError(Exception):
    pass


class RevisionLimitError(AgentError):
    pass


class SpecRefusedError(AgentError):
    pass


class ApprovalRequiredError(AgentError):
    pass


def _rules():
    return list(get_db().constraints.find({}, {"_id": 0}))


def _policy_version() -> int:
    return max([r.get("version", 1) for r in _rules()] or [1])


def _diff(old: Optional[dict], new: dict) -> list:
    if not old:
        return []
    return [{"field": k, "from": old.get(k), "to": v} for k, v in new.items()
            if k not in ("rationale",) and old.get(k) != v]


def _build_prompt(request_text: str, recalled: dict, rules: list) -> str:
    parts = [f"Customer request: {request_text}"]
    if recalled["preferences"]:
        parts.append("Customer memory (promoted preferences): " +
                     "; ".join(f"{p['rule']} (conf {p['confidence']})" for p in recalled["preferences"]))
    if recalled["similar_episodes"]:
        parts.append("Relevant past feedback: " +
                     "; ".join(f"{e['verdict']}: {e['reason_text']}" for e in recalled["similar_episodes"]))
    parts.append("Manufacturing constraints: " + "; ".join(r["description"] for r in rules))
    return "\n".join(parts)


def _generate_spec(prompt: str, context: dict) -> RingSpec:
    last = None
    for _ in range(2):
        try:
            return RingSpec(**llm.complete_json("design", DESIGN_SYSTEM, prompt, context))
        except (ValidationError, ValueError, TypeError) as exc:
            last = exc
    raise SpecRefusedError(f"LLM output failed schema validation twice: {last}")


def generate_design(customer_id: str, request_text: str, session_id: Optional[str] = None,
                    memory_on: bool = True, persist: bool = True) -> dict:
    db = get_db()
    rules = _rules()
    session_id = session_id or uuid.uuid4().hex
    parent = None
    if persist:
        db.customers.update_one({"id": customer_id},
                                {"$setOnInsert": {"id": customer_id, "consent": True, "created_ts": time.time()}},
                                upsert=True)
        existing = list(db.designs.find({"session_id": session_id}, {"_id": 0}).sort("design_version", 1))
        if len(existing) >= 1 + MAX_REVISIONS:
            log_decision(customer_id, "revision_limit_reached", None, session_id=session_id, max=MAX_REVISIONS)
            raise RevisionLimitError(f"Maximum of {MAX_REVISIONS} revisions per session reached")
        parent = existing[-1] if existing else None
        db.design_sessions.update_one({"id": session_id}, {"$set": {"id": session_id, "customer_id": customer_id,
                                                                    "last_request": request_text,
                                                                    "updated_ts": time.time()}}, upsert=True)

    recalled = (memory.recall(customer_id, request_text) if memory_on
                else {"preferences": [], "similar_episodes": []})
    prompt = _build_prompt(request_text, recalled, rules)
    context = {"request": request_text, "preferences": recalled["preferences"]}
    spec = _generate_spec(prompt, context)

    validation = validate(spec, rules)
    fixes = []
    initial_violations = validation["violations"]
    if not validation["valid"]:
        spec, fixes = auto_fix(spec, rules)
        validation = validate(spec, rules)

    memory_refs = [{"memory_id": p["id"], "rule": p["rule"]} for p in recalled["preferences"]] + \
                  [{"episode_id": e["id"], "reason": e["reason_text"]} for e in recalled["similar_episodes"]]
    spec_dict = spec.model_dump()
    design = {
        "id": uuid.uuid4().hex,
        "customer_id": customer_id,
        "session_id": session_id,
        "design_version": (parent["design_version"] + 1) if parent else 1,
        "parent_design_id": parent["id"] if parent else None,
        "request_text": request_text,
        "spec": spec_dict,
        "validation": validation,
        "initial_violations": initial_violations,
        "fixes": fixes,
        "memory_on": memory_on,
        "memory_refs": memory_refs,
        "changed_because": [m["rule"] for m in memory_refs if "rule" in m],
        "diff_vs_parent": _diff(parent["spec"] if parent else None, spec_dict),
        "policy_version": _policy_version(),
        "approval_status": "pending_customer",
        "prompt_tokens_est": max(1, len(prompt) // 4),
        "estimated_weight_g": estimate_weight_g(spec),
        "created_ts": time.time(),
    }
    if not persist:
        return design

    db.designs.insert_one(dict(design))
    log_decision(customer_id, "memory_retrieved", design["id"], memory_on=memory_on, memory_refs=memory_refs)
    log_decision(customer_id, "design_generated", design["id"], design_version=design["design_version"],
                 spec=spec_dict, rationale=spec.rationale, prompt_tokens_est=design["prompt_tokens_est"])
    log_decision(customer_id, "constraints_checked", design["id"], policy_version=design["policy_version"],
                 initial_violations=initial_violations, fixes=fixes, valid=validation["valid"],
                 note="manufacturing rules override request/preferences" if fixes else "no violations")
    return design


def _bom(spec: dict) -> dict:
    db = get_db()
    metal = db.components.find_one({"kind": "metal", "name": spec["metal"]}, {"_id": 0})
    grams = estimate_weight_g(RingSpec(**spec))
    metal_cost = round(grams * metal["price_per_g"], 2)
    stone_cost = 0.0
    stone = None
    if spec["stone_shape"] != "none":
        s = db.components.find_one({"kind": "stone", "name": spec["stone_shape"]}, {"_id": 0})
        stone_cost = round(spec["stone_diameter_mm"] * s["price_per_mm"], 2)
        stone = {"component_id": s["id"], "diameter_mm": spec["stone_diameter_mm"], "cost": stone_cost}
    labor = 25.0
    return {"metal": {"component_id": metal["id"], "grams": grams, "cost": metal_cost}, "stone": stone,
            "labor": labor, "total_cost": round(metal_cost + stone_cost + labor, 2)}


def handle_feedback(design_id: str, verdict: str, reason_text: str = "") -> dict:
    db = get_db()
    design = db.designs.find_one({"id": design_id}, {"_id": 0})
    if not design:
        raise AgentError("design not found")
    cid = design["customer_id"]
    episode_id = memory.record_episode(cid, design_id, verdict, reason_text, design["spec"])
    learned = None
    job = None
    if verdict == "reject":
        db.designs.update_one({"id": design_id}, {"$set": {"approval_status": "rejected"}})
        if reason_text:
            learned = memory.learn_from_rejection(cid, design_id, reason_text, episode_id)
    else:
        db.designs.update_one({"id": design_id}, {"$set": {"approval_status": "customer_accepted"}})
        if design["validation"]["valid"]:
            job = {"id": uuid.uuid4().hex, "design_id": design_id, "customer_id": cid,
                   "bom": _bom(design["spec"]), "policy_version": design["policy_version"],
                   "status": "pending_human_approval", "created_ts": time.time()}
            db.manufacturing_jobs.insert_one(dict(job))
            log_decision(cid, "manufacturing_job_created", design_id, job_id=job["id"], bom=job["bom"])
    db.evaluations.insert_one({
        "id": uuid.uuid4().hex, "design_id": design_id, "customer_id": cid,
        "design_version": design["design_version"], "memory_on": design["memory_on"],
        "memory_ref_count": len(design["memory_refs"]), "verdict": verdict,
        "constraint_fixes": len(design["fixes"]), "prompt_tokens_est": design["prompt_tokens_est"],
        "ts": time.time()})
    log_decision(cid, "evaluation_recorded", design_id, verdict=verdict, memory_on=design["memory_on"])
    return {"design_id": design_id, "verdict": verdict, "learned_memory": learned, "manufacturing_job": job}


def approve_job(job_id: str, approver: str = "human") -> dict:
    db = get_db()
    job = db.manufacturing_jobs.find_one({"id": job_id}, {"_id": 0})
    if not job:
        raise AgentError("job not found")
    db.manufacturing_jobs.update_one({"id": job_id}, {"$set": {"status": "approved", "approved_by": approver,
                                                               "approved_ts": time.time()}})
    db.designs.update_one({"id": job["design_id"]}, {"$set": {"approval_status": "approved_for_manufacturing"}})
    design = db.designs.find_one({"id": job["design_id"]}, {"_id": 0})
    db.products.update_one({"design_id": design["id"]}, {"$set": {
        "design_id": design["id"], "sku": f"AC-{design['id'][:8].upper()}", "price": round(job["bom"]["total_cost"] * 2.5, 2),
        "state": "ready_to_print", "design_version": design["design_version"],
        "memory_refs": design["memory_refs"], "policy_version": design["policy_version"],
        "approval_status": "approved_for_manufacturing"}}, upsert=True)
    log_decision(job["customer_id"], "manufacturing_approved", job["design_id"], job_id=job_id, approver=approver)
    return db.manufacturing_jobs.find_one({"id": job_id}, {"_id": 0})


def export_design(design_id: str) -> dict:
    db = get_db()
    design = db.designs.find_one({"id": design_id}, {"_id": 0})
    if not design:
        raise AgentError("design not found")
    if design["approval_status"] != "approved_for_manufacturing":
        log_decision(design["customer_id"], "export_blocked", design_id, reason="human approval required")
        raise ApprovalRequiredError("STL export requires human manufacturing approval")
    info = export_stl(RingSpec(**design["spec"]), design_id)
    log_decision(design["customer_id"], "stl_exported", design_id, **info)
    return info


def compare_memory(customer_id: str, request_text: str) -> dict:
    on = generate_design(customer_id, request_text, memory_on=True, persist=False)
    off = generate_design(customer_id, request_text, memory_on=False, persist=False)
    return {
        "memory_on": {k: on[k] for k in ("spec", "validation", "fixes", "memory_refs", "prompt_tokens_est")},
        "memory_off": {k: off[k] for k in ("spec", "validation", "fixes", "memory_refs", "prompt_tokens_est")},
        "diff": _diff(off["spec"], on["spec"]),
    }
