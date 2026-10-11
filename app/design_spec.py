from typing import List, Literal

from pydantic import BaseModel, Field


class RingSpec(BaseModel):
    band_width_mm: float = Field(ge=0, le=50)
    band_thickness_mm: float = Field(ge=0, le=20)
    inner_diameter_mm: float = Field(ge=0, le=60)
    profile: Literal["flat", "domed", "comfort"] = "domed"
    stone_shape: Literal["none", "round", "oval"] = "none"
    stone_diameter_mm: float = Field(default=0, ge=0, le=30)
    setting_height_mm: float = Field(default=0, ge=0, le=30)
    metal: Literal["silver", "gold", "platinum"] = "silver"
    style_tags: List[str] = Field(default_factory=list)
    rationale: str = ""


METAL_DENSITY_G_CM3 = {"silver": 10.36, "gold": 19.3, "platinum": 21.45}

DEFAULT_RULES = [
    {"id": "min_thickness", "kind": "min", "field": "band_thickness_mm", "value": 1.2,
     "description": "Band thickness must be at least 1.2 mm to survive printing and casting"},
    {"id": "min_width", "kind": "min", "field": "band_width_mm", "value": 2.0,
     "description": "Band width must be at least 2.0 mm"},
    {"id": "diameter_range", "kind": "range", "field": "inner_diameter_mm", "min": 14.0, "max": 23.0,
     "description": "Inner diameter must be 14-23 mm (US size ~3-13)"},
    {"id": "stone_ratio", "kind": "ratio", "field": "stone_diameter_mm", "ref": "band_width_mm", "value": 2.5,
     "description": "Stone diameter must be <= 2.5x band width"},
    {"id": "max_setting", "kind": "max", "field": "setting_height_mm", "value": 6.0,
     "description": "Setting height must be <= 6 mm"},
    {"id": "max_weight", "kind": "weight", "value": 15.0,
     "description": "Estimated band weight must be <= 15 g"},
]
