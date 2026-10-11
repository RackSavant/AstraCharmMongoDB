import pytest
from fastapi.testclient import TestClient

from app import db
from app.main import app


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("MOCK_LLM", "true")
    monkeypatch.setenv("MONGODB_URI", "")
    monkeypatch.setenv("EXPORT_DIR", str(tmp_path))
    db.reset_connection(None)
    yield TestClient(app)
    db.reset_connection(None)


def test_memory_loop_end_to_end(client):
    v1 = client.post("/designs", json={"customer_id": "ana", "request_text": "celestial moon charm bead"}).json()
    assert v1["design_version"] == 1 and v1["spec"]["outer_diameter_mm"] == 13.0 and v1["spec"]["motif"] == "moon"

    fb = client.post(f"/designs/{v1['id']}/feedback",
                     json={"verdict": "reject", "reason_text": "too big, oversized for my bracelet"}).json()
    assert fb["learned_memory"]["value"] == "compact"

    v2 = client.post("/designs", json={"customer_id": "ana", "request_text": "celestial moon charm bead",
                                       "session_id": v1["session_id"]}).json()
    assert v2["design_version"] == 2 and v2["parent_design_id"] == v1["id"]
    assert v2["spec"]["outer_diameter_mm"] < v1["spec"]["outer_diameter_mm"]
    assert v2["changed_because"] and v2["validation"]["valid"]

    fb2 = client.post(f"/designs/{v2['id']}/feedback", json={"verdict": "accept"}).json()
    job = fb2["manufacturing_job"]
    assert job["status"] == "pending_human_approval"
    assert job["bom"]["print_profile"]["infill_percent"] == 100

    assert client.post(f"/designs/{v2['id']}/export").status_code == 409
    client.post(f"/jobs/{job['id']}/approve")
    exp = client.post(f"/designs/{v2['id']}/export")
    assert exp.status_code == 200 and exp.json()["watertight"]
    assert client.get(f"/designs/{v2['id']}/stl").status_code == 200


def test_constraint_overrides_request_and_isolation(client):
    d = client.post("/designs", json={"customer_id": "bo", "request_text": "star bead 9mm"}).json()
    assert d["spec"]["outer_diameter_mm"] >= 11.5 and d["validation"]["valid"]
    assert any(v["rule_id"] == "min_wall" for v in d["initial_violations"])
    assert client.get("/customers/other/memory").json()["memories"] == []


def test_revision_limit(client):
    sid = None
    for _ in range(3):
        r = client.post("/designs", json={"customer_id": "cy", "request_text": "bead", "session_id": sid})
        assert r.status_code == 200
        sid = r.json()["session_id"]
    assert client.post("/designs", json={"customer_id": "cy", "request_text": "bead", "session_id": sid}).status_code == 429


def test_compare_memory_on_off(client):
    d = client.post("/designs", json={"customer_id": "di", "request_text": "heart bead"}).json()
    client.post(f"/designs/{d['id']}/feedback", json={"verdict": "reject", "reason_text": "too chunky"})
    cmp = client.post("/compare", json={"customer_id": "di", "request_text": "heart bead"}).json()
    assert cmp["memory_on"]["spec"]["outer_diameter_mm"] < cmp["memory_off"]["spec"]["outer_diameter_mm"]
