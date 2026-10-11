# Astra OS (Astra Charms)

A persistent commerce agent that remembers rejections, changes its next design, enforces manufacturing
constraints, logs every decision, and exports a printable STL after human approval.
MongoDB Atlas is the memory, state and governance layer. The LLM is swappable (`app/llm.py`).

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
