import pytest

from app.design_spec import RingSpec
from app.validator import auto_fix, validate


def base(**kw):
    d = dict(band_width_mm=4, band_thickness_mm=2, inner_diameter_mm=17, stone_shape="round",
             stone_diameter_mm=5, setting_height_mm=4, metal="silver")
    d.update(kw)
    return RingSpec(**d)


def test_valid_spec():
    assert validate(base())["valid"]


@pytest.mark.parametrize("kw,rule", [
    ({"band_thickness_mm": 0.8}, "min_thickness"),
    ({"band_width_mm": 1.0, "stone_shape": "none", "stone_diameter_mm": 0}, "min_width"),
    ({"inner_diameter_mm": 30}, "diameter_range"),
    ({"inner_diameter_mm": 10}, "diameter_range"),
    ({"stone_diameter_mm": 12}, "stone_ratio"),
    ({"setting_height_mm": 8}, "max_setting"),
    ({"band_width_mm": 12, "band_thickness_mm": 5, "metal": "platinum", "stone_diameter_mm": 5}, "max_weight"),
])
def test_rule_violations_named(kw, rule):
    res = validate(base(**kw))
    assert rule in [v["rule_id"] for v in res["violations"]]


def test_auto_fix_makes_spec_valid():
    bad = base(band_thickness_mm=0.8, stone_diameter_mm=12, setting_height_mm=9)
    fixed, fixes = auto_fix(bad)
    assert validate(fixed)["valid"]
    assert {f["rule_id"] for f in fixes} >= {"min_thickness", "stone_ratio", "max_setting"}


def test_auto_fix_weight():
    bad = base(band_width_mm=12, band_thickness_mm=5, metal="platinum")
    fixed, fixes = auto_fix(bad)
    assert validate(fixed)["valid"]
    assert any(f["rule_id"] == "max_weight" for f in fixes)
