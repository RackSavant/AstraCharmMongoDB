import json

import pytest

from app import geometry
from app.design_spec import CharmSpec
from app.stl_generator import build_mesh, export_stl


@pytest.mark.parametrize("od,w", [(11.5, 10.5), (13.0, 11.5), (14.0, 12.0)])
@pytest.mark.parametrize("grooves", [0, 3])
def test_export_watertight_and_dimensions(tmp_path, monkeypatch, od, w, grooves):
    monkeypatch.setenv("EXPORT_DIR", str(tmp_path))
    spec = CharmSpec(outer_diameter_mm=od, bead_width_mm=w, groove_count=grooves,
                     groove_depth_mm=0.25 if grooves else 0.0)
    info = export_stl(spec, f"t_{od}_{grooves}")
    assert info["watertight"] and info["volume_mm3"] > 0
    ex = info["bounding_box_mm"]
    assert abs(ex[0] - od) < 0.05 and abs(ex[1] - od) < 0.05 and abs(ex[2] - w) < 0.05
    assert abs(info["volume_mm3"] - geometry.volume_mm3(spec)) / info["volume_mm3"] < 0.01
    assert (tmp_path / f"t_{od}_{grooves}.stl").exists()
    sidecar = json.loads((tmp_path / f"t_{od}_{grooves}.print.json").read_text())
    assert sidecar["print_profile"]["infill_percent"] == 100
    assert sidecar["print_profile"]["layer_height_mm"] <= 0.1


def test_sits_on_build_plate():
    mesh = build_mesh(CharmSpec(outer_diameter_mm=11.5, bead_width_mm=10.5))
    assert abs(mesh.bounds[0][2]) < 1e-6
