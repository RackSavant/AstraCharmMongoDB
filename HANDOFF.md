# HANDOFF: notes for Astra (GPT-6) to finish the job

Goal for tomorrow: run the full loop against **real Astra-6 + MongoDB Atlas + Voyage** and end with a
**physically 3D-printed, customized bead** that slides on a bangle.

Demo sequence that must work reliably:
request -> generated design -> customer rejection -> persistent memory -> improved design -> validated spec -> human approval -> STL -> print.

## 1. Current state (verified)
- 27 pytest tests pass (`.venv/bin/python -m pytest -q`) using `MOCK_LLM=true` and in-memory mongomock.
- Full loop works offline: `tests/test_demo_loop.py`.
- Code layout (`app/`):
  - `design_spec.py`: `CharmSpec`, `DEFAULT_RULES` (manufacturing constraints), `PRINT_PROFILE`, `TOLERANCES`, material densities.
  - `geometry.py`: closed (r,z) bead profile, wall/land/volume math. Shared by validator and STL.
  - `validator.py`: `validate()`, `auto_fix()`, `estimate_weight_g()`.
  - `stl_generator.py`: revolves the profile (trimesh), checks watertight, writes `exports/<id>.stl` and `<id>.print.json`.
  - `memory.py`: episodic record, candidate -> evaluate -> promote, vector recall, delete.
  - `agent.py`: `generate_design`, `handle_feedback`, `approve_job`, `export_design`, `compare_memory`. Max 2 revisions per session.
  - `llm.py`: the ONLY place that calls Astra-6 and Voyage. Contains mock branches.
  - `db.py`: Mongo connection (Atlas if `MONGODB_URI` set, else mongomock), seeding, reset.
  - `main.py`: FastAPI endpoints + static inspector UI (`static/index.html`).
  - `scripts/setup_indexes.py`: creates Atlas vector index `feedback_vec`.

## 2. What is NOT done (in priority order)

### P0: required for the end-to-end print
1. **Connect real Astra-6** in `app/llm.py::complete_json`.
   - Currently assumes an OpenAI-compatible `POST {ASTRA_BASE_URL}/chat/completions` with Bearer `ASTRA_API_KEY`. This is an assumption; fix to the real API/Responses format.
   - Must return a dict. For `task="design"` the keys must match `CharmSpec`; for `task="extract_preference"` return `{key, value, rule}` or `{}`.
   - Enforce JSON-only output (response_format / schema). `_extract_json` strips code fences as a fallback.
   - Set `MOCK_LLM=false` in `.env`. Keep mock mode working for tests.
   - Verify: the rationale from the model is sensible, and `_generate_spec` retries once then refuses (`SpecRefusedError`, HTTP 422).
2. **Connect Atlas.** Put `MONGODB_URI` in `.env` (never commit it), run `python scripts/setup_indexes.py`.
   - Vector index: `feedback_vec` on `feedback.embedding`, 1024 dims, cosine, filter on `customer_id`. Dimensions must match the Voyage model (`voyage-3` = 1024; change `DIMENSIONS` in the script if the model changes).
   - Atlas Search indexes build asynchronously; wait until queryable before testing recall.
   - Verify recall via `$vectorSearch` works (fallback to error log `vector_search_fallback` in `agent_events` means it failed).
   - **Prove persistence:** reject a design, restart the server, confirm `GET /customers/{id}/memory` still returns the memory. This is the headline demo step.
3. **Voyage embeddings**: set `VOYAGE_API_KEY`, confirm `llm.embed` works and a mock-embedded doc is not mixed with real-embedded docs (reset the DB via `POST /demo/reset` when switching).
4. **Real-model behavior check.** The mock LLM is deterministic; a real model may:
   - produce values outside the rules (should be caught by `validate`/`auto_fix`; confirm the log shows `initial_violations` and `fixes`);
   - not visibly change the design after a rejection. If so, strengthen the prompt in `agent._build_prompt` / `DESIGN_SYSTEM` (state clearly that stored preferences must be applied and what changed).
   - extract preferences outside the whitelist in `memory.ALLOWED_PREFERENCES` (size|pattern|motif). Either widen the whitelist or improve `EXTRACT_SYSTEM`.
5. **Print a test bead.** See section 4.

### P1: strongly recommended
6. **Motif geometry.** `motif` (moon|star|heart) is a catalog tag only. Every bead is a plain barrel (+ optional grooves). For a visibly "customized" bead, add raised/engraved relief. Options without boolean libs: add `manifold3d` to requirements for mesh unions/differences, then emboss a small extruded motif on the equator wall; keep relief <= 0.3 mm (see `groove_depth` rule) and keep the 0.5 mm flat land. Add a validator rule + test for it.
7. **Authentication / customer isolation.** `customer_id` is trusted input. For the pitch, use verified user + session IDs. If using Atlas Agent Engine memory, avoid a shared service-account identity across shoppers.
8. **Atlas Agent Engine** (public preview): not integrated. Standard Atlas collections are the fallback and are what the demo uses. If integrating, put it behind the same `memory.py` interface and write important preferences directly (do not wait for async extraction).
9. **Memory ON/OFF comparison** (`POST /compare`, UI button): verify with the real model and confirm token estimate reflects retrieved memory only. `prompt_tokens_est` is a `len/4` estimate, not real usage; replace with real usage from the API response if available.
10. **Measure improvement.** `evaluations` collection stores verdicts per design. Add a simple view/endpoint: acceptance rate with memory ON vs OFF.

### P2: nice to have
11. **REMINDER: make the demo video with Runway** (screen-record the demo script in section 6, then edit/polish in Runway).
12. Voice (ElevenLabs), storefront polish (Next.js), Vercel deploy, deployed backend.
13. Preference decay/confidence lowering over time; handling of conflicting preferences (currently newer preference for the same key replaces the old one and logs `memory_superseded`).
14. Material price table (`db.COMPONENTS`) and pricing multiplier in `agent.approve_job` (x2.5) are placeholders.

## 3. Known issues / decisions to remember
- **Spec geometry conflict:** a true sphere (OD 11.5, width 10.5) has a flat face radius of ~2.35 mm, smaller than the hole radius (2.5 mm), so flats and the 0.5 mm fillet are impossible. We use a **barrel** profile (straight wall, rounded corners, default radius 2.0 mm). Rule `face_land` requires >= 0.5 mm flat land beside the fillet. Documented in README. If a rounder look is wanted, switch to an elliptical profile in `geometry.profile_points` and re-run tests.
- `max_weight` rule (20 g) makes large solid gold beads invalid and **not auto-fixable**; such designs get `validation.valid=false` and no manufacturing job is created.
- Constraints are seeded once into the `constraints` collection. Editing `DEFAULT_RULES` does NOT update an existing database; call `db.reset_db(clear_constraints=True)` or edit the docs (bump `version` for `policy_version`).
- Components are seeded once; `kind` is `material` (older `metal` docs are not used).
- Mock mode uses mongomock: data is NOT persistent across restarts.
- STL is a single watertight revolved body. Printing uses `exports/<id>.print.json` (not auto-sent to a slicer).
- Export is blocked (HTTP 409) until a human approves the manufacturing job (`POST /jobs/{id}/approve`). This is intentional governance.

## 4. Print checklist (end goal)
Reference dimensions: hole 5.0 mm (+0.1/-0.0), OD 11.5 mm (+/-0.2), width 10.5 mm (+/-0.1), wall >= 3.25 mm, 0.5 mm hole-rim fillet.
1. Run the loop, accept a design, approve the job, export (`POST /designs/{id}/export`), download `GET /designs/{id}/stl`.
2. Open the STL in the slicer (PrusaSlicer/Cura/Formlabs PreForm). Confirm: no errors, dimensions correct, hole axis vertical.
3. Slicing: print flat on a face (as exported), **no supports**, **100% infill**, **layer height <= 0.1 mm**. Resin (SLA/DLP) is the best fit for these layer heights; FDM will be rough.
4. Print one **test bead first** and measure the hole with a 4.5 mm endcap/pin and the actual bangle (3.0 mm thick). If it is tight, raise `hole_range` max/target slightly (rule max 5.1) or ream; if loose, reduce toward 5.0. Account for the specific printer shrinkage.
5. Wet sand 800-2000 grit; check the hole rim fillet for sharp edges that could scratch the bangle.
6. Record measured vs target dimensions (add to this file) and adjust `TOLERANCES` / rules if needed.
7. Casting path (silver/gold): print in castable resin, then cast; weight and density are in `validator.estimate_weight_g`.

## 5. Quick commands
```
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
cp .env.example .env            # then fill MONGODB_URI, ASTRA_API_KEY, ASTRA_BASE_URL, VOYAGE_API_KEY; set MOCK_LLM=false
.venv/bin/python -m pytest -q   # must stay green (mock mode)
.venv/bin/python scripts/setup_indexes.py
.venv/bin/uvicorn app.main:app --reload   # http://localhost:8000
```
API flow: `POST /designs` -> `POST /designs/{id}/feedback` (reject with reason) -> `POST /designs` (same `session_id`) -> feedback accept -> `POST /jobs/{id}/approve` -> `POST /designs/{id}/export` -> `GET /designs/{id}/stl`.
Reset between takes: `POST /demo/reset`.

## 6. Demo script (3 min)
1. Request "celestial moon charm bead" -> v1 (13 mm in mock).
2. Reject: "too big, oversized for my bracelet" -> memory panel shows promoted preference.
3. **Restart the server** -> memory still present (Atlas).
4. Request again (same session) -> v2 smaller, `changed_because` cites the memory.
5. Request something illegal ("star bead 9mm") -> manufacturing rule overrides, logged in trace.
6. Memory ON vs OFF comparison.
7. Accept -> job -> human approve -> export STL -> show the printed bead.

## 7. Credentials needed from the owner
- `MONGODB_URI` (Atlas), `VOYAGE_API_KEY`, `ASTRA_API_KEY`, `ASTRA_BASE_URL` plus Astra-6 request/response format. Keep them in `.env` only (gitignored).

## 8. Definition of done
- [ ] Real Astra-6 generates specs that pass `CharmSpec` validation
- [ ] Memory persists across server restart in Atlas; vector recall confirmed
- [ ] Rejection visibly changes the next design with a cited reason
- [ ] Constraint violation is auto-fixed and logged
- [ ] Human approval gate enforced before STL export
- [ ] Test bead printed, measured, fits the bangle
- [ ] Customized bead printed (preferably with motif geometry)
- [ ] `pytest` still green
