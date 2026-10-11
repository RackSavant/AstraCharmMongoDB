import math
from typing import Dict, List, Optional

from app import geometry
from app.design_spec import DEFAULT_RULES, MATERIAL_DENSITY_G_CM3, CharmSpec


def estimate_weight_g(spec: CharmSpec) -> float:
    return round(geometry.volume_mm3(spec) / 1000 * MATERIAL_DENSITY_G_CM3[spec.material], 3)


def _check(rule: dict, spec: CharmSpec) -> Optional[str]:
    kind = rule["kind"]
    if kind == "range":
        val = getattr(spec, rule["field"])
        if not (rule["min"] <= val <= rule["max"]):
            return f"{rule['field']}={val} outside [{rule['min']}, {rule['max']}]"
    elif kind == "min":
        val = getattr(spec, rule["field"])
        if val < rule["value"]:
            return f"{rule['field']}={val} < {rule['value']}"
    elif kind == "max":
        val = getattr(spec, rule["field"])
        if val > rule["value"]:
            return f"{rule['field']}={val} > {rule['value']}"
    elif kind == "wall":
        w = geometry.wall_mm(spec)
        if w < rule["value"]:
            return f"wall {round(w, 3)} mm < {rule['value']} mm"
    elif kind == "width_vs_od":
        limit = spec.outer_diameter_mm - rule["value"]
        if spec.bead_width_mm > limit:
            return f"bead_width_mm={spec.bead_width_mm} > outer_diameter_mm - {rule['value']} ({round(limit, 3)})"
    elif kind == "corner_vs_width":
        if spec.corner_radius_mm > spec.bead_width_mm / 2:
            return f"corner_radius_mm={spec.corner_radius_mm} > bead_width_mm/2"
    elif kind == "land":
        land = geometry.face_land_mm(spec)
        if land < rule["value"]:
            return f"flat land {round(land, 3)} mm < {rule['value']} mm"
    elif kind == "groove_fit":
        if spec.groove_count > 0:
            spacing = geometry.straight_length(spec) / (spec.groove_count + 1)
            if spacing < rule["value"]:
                return f"groove spacing {round(spacing, 3)} mm < {rule['value']} mm"
    elif kind == "weight":
        w = estimate_weight_g(spec)
        if w > rule["value"]:
            return f"estimated weight {w}g > {rule['value']}g"
    return None


def validate(spec: CharmSpec, rules: Optional[List[dict]] = None) -> Dict:
    rules = rules or DEFAULT_RULES
    violations = []
    for rule in rules:
        msg = _check(rule, spec)
        if msg:
            violations.append({"rule_id": rule["id"], "message": msg, "description": rule.get("description", "")})
    return {"valid": not violations, "violations": violations, "fixes": []}


def auto_fix(spec: CharmSpec, rules: Optional[List[dict]] = None):
    rules = rules or DEFAULT_RULES
    by_id = {r["id"]: r for r in rules}
    d = spec.model_dump()
    fixes: list = []

    def setv(field, new, rule_id):
        new = round(new, 3) if isinstance(new, float) else new
        if d[field] != new:
            fixes.append({"rule_id": rule_id, "field": field, "from": d[field], "to": new})
            d[field] = new

    def clamp(rule_id):
        r = by_id.get(rule_id)
        if r:
            setv(r["field"], min(max(d[r["field"]], r["min"]), r["max"]), rule_id)

    clamp("hole_range")
    clamp("od_range")
    if "min_wall" in by_id:
        need = d["core_hole_mm"] + 2 * by_id["min_wall"]["value"]
        if d["outer_diameter_mm"] < need:
            setv("outer_diameter_mm", need, "min_wall")
    clamp("width_range")
    if "width_vs_od" in by_id:
        limit = d["outer_diameter_mm"] - by_id["width_vs_od"]["value"]
        if d["bead_width_mm"] > limit:
            setv("bead_width_mm", limit, "width_vs_od")
    clamp("fillet_range")
    clamp("corner_range")
    if "corner_vs_width" in by_id and d["corner_radius_mm"] > d["bead_width_mm"] / 2:
        setv("corner_radius_mm", d["bead_width_mm"] / 2, "corner_vs_width")
    if "face_land" in by_id:
        max_corner = d["outer_diameter_mm"] / 2 - (d["core_hole_mm"] / 2 + d["fillet_mm"]) - by_id["face_land"]["value"]
        if d["corner_radius_mm"] > max_corner:
            setv("corner_radius_mm", max_corner, "face_land")
    if "groove_depth" in by_id and d["groove_depth_mm"] > by_id["groove_depth"]["value"]:
        setv("groove_depth_mm", by_id["groove_depth"]["value"], "groove_depth")
    if "groove_fit" in by_id:
        length = d["bead_width_mm"] - 2 * d["corner_radius_mm"]
        n = d["groove_count"]
        while n > 0 and length / (n + 1) < by_id["groove_fit"]["value"]:
            n -= 1
        setv("groove_count", n, "groove_fit")
    if d["groove_count"] == 0:
        d["groove_depth_mm"] = 0.0
    return CharmSpec(**d), fixes
