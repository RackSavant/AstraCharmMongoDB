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
        "band_width_mm": 4.0, "band_thickness_mm": 2.2, "inner_diameter_mm": 17.0,
        "profile": "domed", "stone_shape": "round", "stone_diameter_mm": 5.0,
        "setting_height_mm": 4.0, "metal": "silver", "style_tags": ["elegant"],
        "rationale": "Default balanced design for the request.",
    }
    for m in ("gold", "platinum", "silver"):
        if m in req:
            spec["metal"] = m
            break
    if prefs.get("band") == "thin":
        spec.update(band_width_mm=2.4, band_thickness_mm=1.4, profile="comfort")
        spec["style_tags"] = ["elegant", "delicate"]
        spec["rationale"] = "Thinner band because the customer previously rejected a chunky design."
    if prefs.get("band") == "thick":
        spec.update(band_width_mm=6.0, band_thickness_mm=2.8)
    if prefs.get("stone") == "small":
        spec["stone_diameter_mm"] = 3.0
    if prefs.get("stone") == "none":
        spec.update(stone_shape="none", stone_diameter_mm=0.0, setting_height_mm=0.0)
    if prefs.get("style") == "minimal":
        spec["style_tags"] = list(dict.fromkeys(spec["style_tags"] + ["minimal"]))
    m = re.search(r"(\d+(?:\.\d+)?)\s*mm", req)
    if m:
        spec["band_thickness_mm"] = float(m.group(1))
    return spec


def _mock_preference(context: dict) -> dict:
    t = context.get("reason_text", "").lower()
    if any(w in t for w in ("chunky", "thick", "heavy", "bulky", "delicate", "thin", "dainty")):
        if any(w in t for w in ("want thick", "thicker", "too thin")):
            return {"key": "band", "value": "thick", "rule": "Prefers a thicker, bolder band"}
        return {"key": "band", "value": "thin", "rule": "Prefers a thin, delicate band"}
    if any(w in t for w in ("big stone", "large stone", "stone too big", "flashy", "huge stone")):
        return {"key": "stone", "value": "small", "rule": "Prefers a small stone"}
    if any(w in t for w in ("no stone", "plain")):
        return {"key": "stone", "value": "none", "rule": "Prefers no stone"}
    if "minimal" in t or "simple" in t:
        return {"key": "style", "value": "minimal", "rule": "Prefers a minimal style"}
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
