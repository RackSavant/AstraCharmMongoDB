import os
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from app import agent, db, memory
from app.logger import get_log

app = FastAPI(title="Astra OS")


class DesignRequest(BaseModel):
    customer_id: str
    request_text: str
    session_id: Optional[str] = None
    memory_on: bool = True


class FeedbackRequest(BaseModel):
    verdict: str
    reason_text: str = ""


class CompareRequest(BaseModel):
    customer_id: str
    request_text: str


@app.get("/health")
def health():
    return {"status": "ok", "atlas": db.using_atlas()}


def _clean(doc):
    if isinstance(doc, dict):
        doc.pop("_id", None)
    return doc


@app.post("/designs")
def create_design(req: DesignRequest):
    try:
        return agent.generate_design(req.customer_id, req.request_text, req.session_id, req.memory_on)
    except agent.RevisionLimitError as e:
        raise HTTPException(429, str(e))
    except agent.SpecRefusedError as e:
        raise HTTPException(422, str(e))


@app.get("/designs/{design_id}")
def get_design(design_id: str):
    d = db.get_db().designs.find_one({"id": design_id}, {"_id": 0})
    if not d:
        raise HTTPException(404, "design not found")
    return d


@app.post("/designs/{design_id}/feedback")
def feedback(design_id: str, req: FeedbackRequest):
    if req.verdict not in ("accept", "reject"):
        raise HTTPException(400, "verdict must be accept or reject")
    try:
        return agent.handle_feedback(design_id, req.verdict, req.reason_text)
    except agent.AgentError as e:
        raise HTTPException(404, str(e))


@app.get("/designs/{design_id}/log")
def design_log(design_id: str):
    return get_log(design_id=design_id)


@app.post("/jobs/{job_id}/approve")
def approve(job_id: str):
    try:
        return agent.approve_job(job_id)
    except agent.AgentError as e:
        raise HTTPException(404, str(e))


@app.get("/customers/{customer_id}/jobs")
def jobs(customer_id: str):
    return list(db.get_db().manufacturing_jobs.find({"customer_id": customer_id}, {"_id": 0}))


@app.post("/designs/{design_id}/export")
def export(design_id: str):
    try:
        return agent.export_design(design_id)
    except agent.ApprovalRequiredError as e:
        raise HTTPException(409, str(e))
    except agent.AgentError as e:
        raise HTTPException(404, str(e))


@app.get("/designs/{design_id}/stl")
def download_stl(design_id: str):
    from app import config
    path = os.path.join(config.export_dir(), f"{design_id}.stl")
    if not os.path.exists(path):
        raise HTTPException(404, "STL not exported yet")
    return FileResponse(path, media_type="model/stl", filename=f"{design_id}.stl")


@app.get("/customers/{customer_id}/memory")
def customer_memory(customer_id: str):
    return {
        "memories": memory.list_memories(customer_id),
        "episodes": list(db.get_db().feedback.find({"customer_id": customer_id}, {"_id": 0, "embedding": 0})),
        "evaluations": list(db.get_db().evaluations.find({"customer_id": customer_id}, {"_id": 0})),
    }


@app.delete("/customers/{customer_id}/memory/{memory_id}")
def delete_memory(customer_id: str, memory_id: str):
    if not memory.delete_memory(customer_id, memory_id):
        raise HTTPException(404, "memory not found")
    return {"deleted": memory_id}


@app.get("/customers/{customer_id}/events")
def events(customer_id: str):
    return get_log(customer_id=customer_id)


@app.post("/compare")
def compare(req: CompareRequest):
    return agent.compare_memory(req.customer_id, req.request_text)


@app.get("/constraints")
def constraints():
    return list(db.get_db().constraints.find({}, {"_id": 0}))


@app.post("/demo/reset")
def reset():
    db.reset_db()
    return {"reset": True}


STATIC_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
if os.path.isdir(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

    @app.get("/")
    def index():
        return FileResponse(os.path.join(STATIC_DIR, "index.html"))
