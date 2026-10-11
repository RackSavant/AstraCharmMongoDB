import math
from typing import Dict, List, Optional

from app.design_spec import DEFAULT_RULES, METAL_DENSITY_G_CM3, RingSpec


def estimate_weight_g(spec: RingSpec) -> float:
    r = spec.inner_diameter_mm / 2
    t = spec.band_thickness_mm
    vol_mm3 = math.pi * ((r + t) ** 2 - r ** 2) * spec.band_width_mm
    return round(vol_mm3 / 1000 * METAL_DENSITY_G_CM3[spec.metal], 3)


def _check(rule: dict, spec: RingSpec) -> Optional[str]:
    kind = rule["kind"]
    if kind == "weight":
        w = estimate_weight_g(spec)
        return f"estimated weight {w}g > {rule['value']}g" if w > rule["value"] else None
    val = getattr(spec, rule["field"])
    if kind == "min" and val < rule["value"]:
        return f"{rule['field']}={val} < {rule['value']}"
    if kind == "max" and val > rule["value"]:
        return f"{rule['field']}={val} > {rule['value']}"
    if kind == "range" and not (rule["min"] <= val <= rule["max"]):
        return f"{rule['field']}={val} outside [{rule['min']}, {rule['max']}]"
    if kind == "ratio" and spec.stone_shape != "none":
        limit = getattr(spec, rule["ref"]) * rule["value"]
        if val > limit:
            return f"{rule['field']}={val} > {rule['value']}x {rule['ref']} ({round(limit, 3)})"
    return None


def validate(spec: RingSpec, rules: Optional[List[dict]] = None) -> Dict:
    rules = rules or DEFAULT_RULES
    violations = []
    for rule in rules:
        msg = _check(rule, spec)
        if msg:
            violations.append({"rule_id": rule["id"], "message": msg, "description": rule.get("description", "")})
    return {"valid": not violations, "violations": violations, "fixes": []}


def auto_fix(spec: RingSpec, rules: Optional[List[dict]] = None):
    rules = rules or DEFAULT_RULES
    data = spec.model_dump()
    fixes = []

    def setv(field, new, rule_id):
        old = data[field]
        if old != new:
            data[field] = round(new, 3)
            fixes.append({"rule_id": rule_id, "field": field, "from": old, "to": round(new, 3)})

    by_id = {r["id"]: r for r in rules}
    for rid in ("min_thickness", "min_width"):
        r = by_id.get(rid)
        if r and data[r["field"]] < r["value"]:
            setv(r["field"], r["value"], rid)
    r = by_id.get("diameter_range")
    if r:
        setv(r["field"], min(max(data[r["field"]], r["min"]), r["max"]), "diameter_range")
    r = by_id.get("max_setting")
    if r and data[r["field"]] > r["value"]:
        setv(r["field"], r["value"], "max_setting")
    r = by_id.get("stone_ratio")
    if r and data["stone_shape"] != "none":
        limit = data[r["ref"]] * r["value"]
        if data[r["field"]] > limit:
            setv(r["field"], limit, "stone_ratio")
    r = by_id.get("max_weight")
    if r:
        min_t = by_id.get("min_thickness", {}).get("value", 0)
        min_w = by_id.get("min_width", {}).get("value", 0)
        for _ in range(500):
            if estimate_weight_g(RingSpec(**data)) <= r["value"]:
                break
            if data["band_thickness_mm"] - 0.1 >= min_t:
                data["band_thickness_mm"] = round(data["band_thickness_mm"] - 0.1, 3)
            elif data["band_width_mm"] - 0.1 >= min_w:
                data["band_width_mm"] = round(data["band_width_mm"] - 0.1, 3)
            else:
                break
        orig = spec.model_dump()
        for f in ("band_thickness_mm", "band_width_mm"):
            if orig[f] != data[f] and not any(x["field"] == f and x["rule_id"] == "max_weight" for x in fixes):
                fixes.append({"rule_id": "max_weight", "field": f, "from": orig[f], "to": data[f]})
    return RingSpec(**data), fixes
