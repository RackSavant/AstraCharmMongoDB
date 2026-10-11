import json
import os
from typing import Dict

import numpy as np
import trimesh

from app import config, geometry
from app.design_spec import PRINT_PROFILE, TOLERANCES, CharmSpec


def build_mesh(spec: CharmSpec) -> trimesh.Trimesh:
    pts = np.array(geometry.profile_points(spec))
    mesh = trimesh.creation.revolve(pts, angle=2 * np.pi, sections=96)
    mesh.merge_vertices()
    if mesh.volume < 0:
        mesh.invert()
    mesh.apply_translation([0, 0, -mesh.bounds[0][2]])
    return mesh


def export_stl(spec: CharmSpec, design_id: str) -> Dict:
    mesh = build_mesh(spec)
    if not mesh.is_watertight or mesh.volume <= 0:
        raise ValueError("generated mesh is not printable (not watertight or non-positive volume)")
    os.makedirs(config.export_dir(), exist_ok=True)
    path = os.path.join(config.export_dir(), f"{design_id}.stl")
    mesh.export(path)
    info = {
        "path": path,
        "watertight": True,
        "volume_mm3": round(float(mesh.volume), 3),
        "bounding_box_mm": [round(float(x), 3) for x in mesh.extents],
        "print_profile": PRINT_PROFILE,
        "tolerances": TOLERANCES,
    }
    with open(os.path.join(config.export_dir(), f"{design_id}.print.json"), "w") as fh:
        json.dump({"spec": spec.model_dump(), **info}, fh, indent=2)
    return info
