import os
from typing import Dict

import numpy as np
import trimesh

from app import config
from app.design_spec import RingSpec


def _profile(spec: RingSpec, steps: int = 12) -> np.ndarray:
    r_in = spec.inner_diameter_mm / 2
    t = spec.band_thickness_mm
    w = spec.band_width_mm
    zs = np.linspace(-w / 2, w / 2, steps)
    bulge = {"flat": 0.0, "domed": 0.35 * t, "comfort": 0.2 * t}[spec.profile]
    inner_bulge = 0.2 * t if spec.profile == "comfort" else 0.0
    outer = [(r_in + t + bulge * (1 - (2 * z / w) ** 2), z) for z in zs]
    inner = [(r_in - inner_bulge * (1 - (2 * z / w) ** 2), z) for z in zs[::-1]]
    pts = outer + inner
    pts.append(pts[0])
    return np.array(pts), r_in + t + bulge


def build_mesh(spec: RingSpec) -> trimesh.Trimesh:
    pts, r_top = _profile(spec)
    band = trimesh.creation.revolve(pts, angle=2 * np.pi, sections=96)
    band.merge_vertices()
    if band.volume < 0:
        band.invert()
    parts = [band]
    if spec.stone_shape != "none" and spec.stone_diameter_mm > 0:
        rot = trimesh.transformations.rotation_matrix(np.pi / 2, [0, 1, 0])
        bezel_h = max(spec.setting_height_mm, 0.5)
        bezel = trimesh.creation.cylinder(radius=spec.stone_diameter_mm / 2 + 0.6, height=bezel_h, sections=48)
        bezel.apply_transform(rot)
        bezel.apply_translation([r_top - 0.3 + bezel_h / 2, 0, 0])
        seat = trimesh.creation.cylinder(radius=spec.stone_diameter_mm / 2, height=0.8, sections=48)
        seat.apply_transform(rot)
        seat.apply_translation([r_top - 0.3 + bezel_h + 0.4, 0, 0])
        parts += [bezel, seat]
    return trimesh.util.concatenate(parts) if len(parts) > 1 else band


def export_stl(spec: RingSpec, design_id: str) -> Dict:
    mesh = build_mesh(spec)
    watertight = all(c.is_watertight for c in mesh.split(only_watertight=False))
    if not watertight or mesh.volume <= 0:
        raise ValueError("generated mesh is not printable (not watertight or non-positive volume)")
    os.makedirs(config.export_dir(), exist_ok=True)
    path = os.path.join(config.export_dir(), f"{design_id}.stl")
    mesh.export(path)
    return {
        "path": path,
        "watertight": True,
        "volume_mm3": round(float(mesh.volume), 3),
        "bounding_box_mm": [round(float(x), 3) for x in mesh.extents],
    }
