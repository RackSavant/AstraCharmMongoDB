import hashlib
import json
import math
import re
from typing import List, Optional

import httpx

from app import config

EMBED_DIM_MOCK = 64


def _mock_design(context: dict) -> dict:
    req = context.get("request", "").lower()
    prefs = {p["key"]: p["value"] for p in context.get("preferences", [])}
    spec = {
        "outer_diameter_mm": 13.0, "bead_width_mm": 11.5, "core_hole_mm": 5.0, "fillet_mm": 0.5,
        "corner_radius_mm": 2.0, "groove_count": 0, "groove_depth_mm": 0.0, "motif": "none",
        "material": "resin", "style_tags": ["celestial"],
        "rationale": "Default bold bead for the request.",
    }
    for motif in ("moon", "star", "heart"):
        if motif in req:
            spec["motif"] = motif
            break
    for material in ("gold", "silver", "resin"):
        if material in req:
            spec["material"] = material
            break
    notes = []
    if prefs.get("size") == "compact":
        spec.update(outer_diameter_mm=11.5, bead_width_mm=10.5)
        notes.append("compact size because the customer previously rejected an oversized bead")
    if prefs.get("size") == "bold":
        spec.update(outer_diameter_mm=14.0, bead_width_mm=12.0)
        notes.append("bolder size because the customer previously found a bead too small")
    if prefs.get("pattern") == "grooved":
        spec.update(groove_count=3, groove_depth_mm=0.25)
        notes.append("grooved texture because the customer previously found a bead too plain")
    if prefs.get("pattern") == "smooth":
        spec.update(groove_count=0, groove_depth_mm=0.0)
        notes.append("smooth surface because the customer previously found a bead too busy")
    if prefs.get("motif") and spec["motif"] == "none":
        spec["motif"] = prefs["motif"]
        notes.append(f"{prefs['motif']} motif from remembered preference")
    if notes:
        spec["rationale"] = "Adjusted: " + "; ".join(notes) + "."
    m = re.search(r"(\d+(?:\.\d+)?)\s*mm", req)
    if m:
        spec["outer_diameter_mm"] = float(m.group(1))
    return spec


def _mock_preference(context: dict) -> dict:
    t = context.get("reason_text", "").lower()
    if any(w in t for w in ("too small", "tiny", "bolder", "bigger", "more presence")):
        return {"key": "size", "value": "bold", "rule": "Prefers a bolder, larger bead"}
    if any(w in t for w in ("too big", "oversized", "huge", "large", "chunky", "bulky", "too heavy")):
        return {"key": "size", "value": "compact", "rule": "Prefers a compact bead, not oversized"}
    if any(w in t for w in ("too plain", "boring", "more texture")):
        return {"key": "pattern", "value": "grooved", "rule": "Prefers a textured, grooved surface"}
    if any(w in t for w in ("too busy", "too much texture", "simple", "minimal")):
        return {"key": "pattern", "value": "smooth", "rule": "Prefers a smooth, minimal surface"}
    m = re.search(r"(?:prefer|love|like|want)\s+(?:\w+\s+)?(moon|star|heart)", t)
    if m:
        return {"key": "motif", "value": m.group(1), "rule": f"Prefers the {m.group(1)} motif"}
    return {}


def _extract_json(text: str) -> dict:
    text = text.strip()
    text = re.sub(r"^```(?:json)?|```$", "", text, flags=re.MULTILINE).strip()
    start, end = text.find("{"), text.rfind("}")
    return json.loads(text[start:end + 1])


def complete_json(task: str, system: str, user: str, context: Optional[dict] = None) -> dict:
    """Single entry point for Astra-6. task: 'design' | 'extract_preference'."""
    context = context or {}
    if config.mock_llm():
        return _mock_design(context) if task == "design" else _mock_preference(context)
    if not (config.astra_api_key() and config.astra_base_url()):
        raise RuntimeError("ASTRA_API_KEY and ASTRA_BASE_URL are required when MOCK_LLM=false")
    resp = httpx.post(
        f"{config.astra_base_url()}/chat/completions",
        headers={"Authorization": f"Bearer {config.astra_api_key()}"},
        json={
            "model": config.astra_model(),
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
            "temperature": 0.4,
        },
        timeout=60,
    )
    resp.raise_for_status()
    return _extract_json(resp.json()["choices"][0]["message"]["content"])


def embed(text: str) -> List[float]:
    if config.mock_llm() or not config.voyage_api_key():
        vec = [0.0] * EMBED_DIM_MOCK
        for w in re.findall(r"[a-z]+", text.lower()):
            vec[int(hashlib.md5(w.encode()).hexdigest(), 16) % EMBED_DIM_MOCK] += 1.0
        n = math.sqrt(sum(x * x for x in vec)) or 1.0
        return [x / n for x in vec]
    resp = httpx.post(
        "https://api.voyageai.com/v1/embeddings",
        headers={"Authorization": f"Bearer {config.voyage_api_key()}"},
        json={"input": [text], "model": config.voyage_model()},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()["data"][0]["embedding"]
