# Astra OS (Astra Charms)

A persistent commerce agent that remembers rejections, changes its next design, enforces manufacturing
constraints, logs every decision, and exports a printable STL after human approval.
MongoDB Atlas is the memory, state and governance layer. The LLM is swappable (`app/llm.py`).

> Remaining work and next-session instructions: see [HANDOFF.md](HANDOFF.md).

## Loop
request -> memory recall -> design (JSON spec) -> constraint validation/auto-fix -> customer feedback ->
episode + candidate memory -> evaluate -> promote -> improved next design -> BOM job -> human approval -> STL

## Run
```
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
cp .env.example .env
.venv/bin/python -m pytest -q
.venv/bin/uvicorn app.main:app --reload
```
Open http://localhost:8000. With no `MONGODB_URI` it uses in-memory mongomock (not persistent across restarts).
Set `MONGODB_URI` to use Atlas, then run `python scripts/setup_indexes.py` to create the vector index.

## Charm spec (bangle-compatible barrel bead)
Reference: hole 5.0 mm (+0.1/-0.0), outer diameter 11.5 mm (+/-0.2), width 10.5 mm (+/-0.1),
wall >= 3.25 mm, 0.5 mm fillet on hole rims. Customer-variable: outer diameter (11.5-14), width, corner radius,
grooves (0-4, <= 0.3 mm deep), motif tag (moon|star|heart), material (resin|silver|gold).
Rules live in the `constraints` collection (`app/design_spec.py: DEFAULT_RULES`) and override the LLM.

Geometry note: a true sphere of 11.5 mm cut flat at 10.5 mm has a flat face of radius ~2.35 mm, smaller than the
2.5 mm hole radius, so the flats and the 0.5 mm fillet cannot exist. The bead is therefore a barrel (cylindrical
wall, rounded corners, default radius 2.0 mm) that keeps the 11.5 / 10.5 / 5.0 dimensions and leaves a flat
print-bed land beside the fillet (rule `face_land`, >= 0.5 mm). Motif is a catalog tag only; it is not modeled in 3D yet.

Print profile exported next to each STL (`exports/<id>.print.json`): flat on a face, no supports, 100% infill,
0.1 mm layers, sand 800-2000 grit. The STL is placed on Z=0 with the hole axis vertical.

## Config (`.env`)
- `MOCK_LLM=true` deterministic offline mode. Set `false` and fill `ASTRA_API_KEY` + `ASTRA_BASE_URL` for the real model
  (`app/llm.py` assumes an OpenAI-compatible `/chat/completions`; adjust if Astra-6 differs).
- `VOYAGE_API_KEY` for real embeddings (1024 dims, `voyage-3`); mock hash embeddings otherwise.

## Collections
customers, products, designs, design_sessions, agent_events, feedback (episodic, embedded), memories (semantic),
constraints (procedural), components, manufacturing_jobs, evaluations.

## Governance
- Schema-validated LLM output (one retry, else refusal)
- Memory whitelist + candidate -> evaluate -> promote
- Deterministic manufacturing rules override requests
- Max 2 revisions per session
- STL export blocked until human approves the manufacturing job
- Customers can delete memories; all actions logged in `agent_events`

## Status / not yet done
- Atlas Agent Engine is not integrated (public preview); standard Atlas collections are the fallback.
- No customer auth; `customer_id` is trusted input.
