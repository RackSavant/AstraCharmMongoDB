import math
from typing import List, Tuple

from app.design_spec import GROOVE_HALF_WIDTH_MM, CharmSpec

Point = Tuple[float, float]


def straight_length(spec: CharmSpec) -> float:
    return spec.bead_width_mm - 2 * spec.corner_radius_mm


def wall_mm(spec: CharmSpec) -> float:
    return (spec.outer_diameter_mm - spec.core_hole_mm) / 2


def face_land_mm(spec: CharmSpec) -> float:
    return (spec.outer_diameter_mm / 2 - spec.corner_radius_mm) - (spec.core_hole_mm / 2 + spec.fillet_mm)


def _arc(cx: float, cz: float, radius: float, a0: float, a1: float, steps: int) -> List[Point]:
    return [(cx + radius * math.cos(math.radians(a0 + (a1 - a0) * i / steps)),
             cz + radius * math.sin(math.radians(a0 + (a1 - a0) * i / steps))) for i in range(steps + 1)]


def profile_points(spec: CharmSpec, arc_steps: int = 12) -> List[Point]:
    """Closed counter-clockwise (r, z) cross-section; revolve about Z to get the bead."""
    R = spec.outer_diameter_mm / 2
    rh = spec.core_hole_mm / 2
    h = spec.bead_width_mm / 2
    c = spec.corner_radius_mm
    f = spec.fillet_mm
    pts: List[Point] = [(rh, h - f)]
    pts += _arc(rh + f, -h + f, f, 180, 270, arc_steps)
    pts += _arc(R - c, -h + c, c, 270, 360, arc_steps)
    n = spec.groove_count
    length = straight_length(spec)
    for i in range(n):
        zc = -(h - c) + length * (i + 1) / (n + 1)
        pts += [(R, zc - GROOVE_HALF_WIDTH_MM), (R - spec.groove_depth_mm, zc), (R, zc + GROOVE_HALF_WIDTH_MM)]
    pts += _arc(R - c, h - c, c, 0, 90, arc_steps)
    pts += _arc(rh + f, h - f, f, 90, 180, arc_steps)
    clean: List[Point] = []
    for p in pts:
        if not clean or math.dist(clean[-1], p) > 1e-9:
            clean.append(p)
    if math.dist(clean[0], clean[-1]) > 1e-9:
        clean.append(clean[0])
    else:
        clean[-1] = clean[0]
    return clean


def volume_mm3(spec: CharmSpec) -> float:
    pts = profile_points(spec)
    cx_area = 0.0
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        cx_area += (x0 + x1) * (x0 * y1 - x1 * y0)
    return abs(2 * math.pi * cx_area / 6)
