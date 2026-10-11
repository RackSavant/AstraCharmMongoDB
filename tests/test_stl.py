import pytest

from app import config
from app.design_spec import RingSpec
from app.stl_generator import export_stl


@pytest.mark.parametrize("profile", ["flat", "domed", "comfort"])
@pytest.mark.parametrize("stone", ["none", "round"])
def test_export_watertight(tmp_path, monkeypatch, profile, stone):
    monkeypatch.setenv("EXPORT_DIR", str(tmp_path))
    spec = RingSpec(band_width_mm=3, band_thickness_mm=1.5, inner_diameter_mm=17, profile=profile,
                    stone_shape=stone, stone_diameter_mm=4 if stone != "none" else 0, setting_height_mm=3)
    info = export_stl(spec, f"t_{profile}_{stone}")
    assert info["watertight"] and info["volume_mm3"] > 0
    assert (tmp_path / f"t_{profile}_{stone}.stl").exists()
