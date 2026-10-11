from typing import List, Literal

from pydantic import BaseModel, Field


class CharmSpec(BaseModel):
    """Bangle-compatible barrel bead charm. All lengths in mm. Axis of the core hole is Z."""

    outer_diameter_mm: float = Field(ge=0, le=60)
    bead_width_mm: float = Field(ge=0, le=60)
    core_hole_mm: float = Field(default=5.0, ge=0, le=20)
    fillet_mm: float = Field(default=0.5, ge=0, le=5)
    corner_radius_mm: float = Field(default=2.0, ge=0, le=10)
    groove_count: int = Field(default=0, ge=0, le=10)
    groove_depth_mm: float = Field(default=0.0, ge=0, le=2)
    motif: Literal["none", "moon", "star", "heart"] = "none"
    material: Literal["resin", "silver", "gold"] = "resin"
    style_tags: List[str] = Field(default_factory=list)
    rationale: str = ""


MATERIAL_DENSITY_G_CM3 = {"resin": 1.1, "silver": 10.36, "gold": 19.3}

GROOVE_HALF_WIDTH_MM = 0.4

TOLERANCES = {
    "core_hole_mm": "+0.1 / -0.0 (CAD target 5.0; bangle needs a 4.5 mm opening, extra clearance covers printer shrinkage)",
    "outer_diameter_mm": "+/-0.2",
    "bead_width_mm": "+/-0.1",
}

PRINT_PROFILE = {
    "orientation": "flat on one flattened core opening, hole axis vertical, no supports",
    "supports": False,
    "infill_percent": 100,
    "layer_height_mm": 0.1,
    "post_processing": "wet sand 800-2000 grit; ream hole to 5.0 mm if tight",
}

DEFAULT_RULES = [
    {"id": "hole_range", "kind": "range", "field": "core_hole_mm", "min": 5.0, "max": 5.1,
     "description": "Core hole 5.0-5.1 mm (+0.1/-0.0) so the 4.5 mm endcaps slide smoothly"},
    {"id": "od_range", "kind": "range", "field": "outer_diameter_mm", "min": 11.5, "max": 14.0,
     "description": "Outer diameter 11.5-14.0 mm to stay proportional with standard charms"},
    {"id": "width_range", "kind": "range", "field": "bead_width_mm", "min": 9.0, "max": 13.0,
     "description": "Bead width 9-13 mm along the bangle"},
    {"id": "width_vs_od", "kind": "width_vs_od", "value": 0.5,
     "description": "Bead width must be at least 0.5 mm below outer diameter so contact faces are flattened"},
    {"id": "min_wall", "kind": "wall", "value": 3.25,
     "description": "Wall between hole and outer edge must be >= 3.25 mm"},
    {"id": "fillet_range", "kind": "range", "field": "fillet_mm", "min": 0.4, "max": 0.8,
     "description": "Hole rim fillet 0.4-0.8 mm (0.5 target) to avoid scratching the bangle"},
    {"id": "corner_range", "kind": "range", "field": "corner_radius_mm", "min": 1.5, "max": 3.0,
     "description": "Outer corner radius 1.5-3.0 mm"},
    {"id": "corner_vs_width", "kind": "corner_vs_width",
     "description": "Corner radius must not exceed half the bead width"},
    {"id": "face_land", "kind": "land", "value": 0.5,
     "description": "Flat bed-contact land beside the hole fillet must be >= 0.5 mm so it prints flat"},
    {"id": "groove_depth", "kind": "max", "field": "groove_depth_mm", "value": 0.3,
     "description": "Groove depth <= 0.3 mm to keep wall and surface quality"},
    {"id": "groove_fit", "kind": "groove_fit", "value": 1.2,
     "description": "Grooves need >= 1.2 mm spacing on the straight wall"},
    {"id": "max_weight", "kind": "weight", "value": 20.0,
     "description": "Estimated bead weight must be <= 20 g"},
]
