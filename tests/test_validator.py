import pytest

from app import geometry
from app.design_spec import CharmSpec
from app.validator import auto_fix, estimate_weight_g, validate


def base(**kw):
    d = dict(outer_diameter_mm=11.5, bead_width_mm=10.5, core_hole_mm=5.0, fillet_mm=0.5,
             corner_radius_mm=2.0, material="resin")
    d.update(kw)
    return CharmSpec(**d)


def test_reference_spec_is_valid():
    res = validate(base())
    assert res["valid"], res["violations"]
    assert geometry.wall_mm(base()) == 3.25


@pytest.mark.parametrize("kw,rule", [
    ({"core_hole_mm": 4.5}, "hole_range"),
    ({"core_hole_mm": 5.3}, "hole_range"),
    ({"outer_diameter_mm": 9.0}, "od_range"),
    ({"outer_diameter_mm": 9.0}, "min_wall"),
    ({"bead_width_mm": 11.5}, "width_vs_od"),
    ({"bead_width_mm": 8.0}, "width_range"),
    ({"fillet_mm": 0.1}, "fillet_range"),
    ({"corner_radius_mm": 3.4}, "corner_range"),
    ({"corner_radius_mm": 2.9}, "face_land"),
    ({"groove_count": 1, "groove_depth_mm": 0.6}, "groove_depth"),
    ({"groove_count": 6, "groove_depth_mm": 0.2}, "groove_fit"),
    ({"outer_diameter_mm": 14.0, "bead_width_mm": 13.0, "material": "gold"}, "max_weight"),
])
def test_rule_violations_named(kw, rule):
    assert rule in [v["rule_id"] for v in validate(base(**kw))["violations"]]


def test_spherical_flatten_is_not_possible_with_reference_numbers():
    sphere_flat_radius = ((11.5 / 2) ** 2 - (10.5 / 2) ** 2) ** 0.5
    assert sphere_flat_radius < 5.0 / 2


def test_auto_fix_makes_spec_valid():
    bad = base(outer_diameter_mm=9.0, bead_width_mm=11.5, core_hole_mm=4.5, fillet_mm=0.1,
               groove_count=6, groove_depth_mm=0.6)
    fixed, fixes = auto_fix(bad)
    assert validate(fixed)["valid"], validate(fixed)["violations"]
    assert {"hole_range", "od_range", "fillet_range", "groove_depth"} <= {f["rule_id"] for f in fixes}


def test_weight_scales_with_material():
    assert estimate_weight_g(base(material="silver")) > estimate_weight_g(base(material="resin")) * 5
