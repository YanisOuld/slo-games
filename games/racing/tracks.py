"""Track geometry. No pygame: pure math, so headless training can use it too.

A track is a closed, smooth centerline (Catmull-Rom spline through a few control
points), resampled every SPACING px, plus a half width. Its two walls are the
centerline pushed out sideways by the half width on each side.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

Point = tuple[float, float]

SPACING = 8.0       # px between centerline samples
DESIGN_W, DESIGN_H = 640, 520  # control points are written in this box


@dataclass(frozen=True)
class TrackSpec:
    name: str
    level: str
    points: tuple[Point, ...]  # control points, in race order (first segment = start straight)
    half_width: float


TRACKS: tuple[TrackSpec, ...] = (
    TrackSpec("Ovale", "Facile", (
        (150, 90), (490, 90), (580, 160), (580, 360), (490, 430), (150, 430), (60, 360), (60, 160),
    ), 40),
    TrackSpec("Serpent", "Moyen", (
        (110, 70), (420, 70), (570, 110), (590, 250), (520, 330), (560, 420), (470, 470),
        (330, 430), (240, 470), (110, 450), (60, 350), (118, 262), (60, 170),
    ), 34),
    TrackSpec("Épingles", "Difficile", (
        (100, 70), (540, 70), (595, 130), (540, 190), (240, 190), (175, 250), (240, 310),
        (540, 310), (595, 370), (540, 440), (130, 450), (60, 400), (50, 250), (60, 120),
    ), 30),
    TrackSpec("Grand Prix", "Expert", (
        (120, 470), (480, 470), (580, 420), (590, 300), (528, 245), (565, 165), (520, 80),
        (380, 60), (300, 130), (220, 70), (100, 90), (60, 200), (150, 280), (80, 370),
    ), 30),
)


def _catmull_rom_closed(points: tuple[Point, ...], steps: int = 24) -> list[Point]:
    n = len(points)
    out = []
    for i in range(n):
        p0, p1, p2, p3 = points[i - 1], points[i], points[(i + 1) % n], points[(i + 2) % n]
        for s in range(steps):
            t = s / steps
            t2, t3 = t * t, t * t * t
            out.append(tuple(
                0.5 * (2 * b + (-a + c) * t + (2 * a - 5 * b + 4 * c - d) * t2 + (-a + 3 * b - 3 * c + d) * t3)
                for a, b, c, d in zip(p0, p1, p2, p3)
            ))
    return out


def _smooth_closed(points: list[Point], radius: int, passes: int) -> list[Point]:
    """Moving average around the loop: rounds off corners that would be too tight
    for the inner wall (which would otherwise fold over itself)."""
    n = len(points)
    for _ in range(passes):
        points = [
            (sum(points[(i + d) % n][0] for d in range(-radius, radius + 1)) / (2 * radius + 1),
             sum(points[(i + d) % n][1] for d in range(-radius, radius + 1)) / (2 * radius + 1))
            for i in range(n)
        ]
    return points


def _resample_closed(points: list[Point], spacing: float) -> list[Point]:
    """Evenly spaced points along the closed polyline (so index ~ distance)."""
    loop = points + [points[0]]
    seg = [math.dist(loop[i], loop[i + 1]) for i in range(len(points))]
    total = sum(seg)
    count = max(3, round(total / spacing))
    step = total / count
    out, i, walked = [], 0, 0.0
    for k in range(count):
        target = k * step
        while walked + seg[i] < target:
            walked += seg[i]
            i += 1
        t = (target - walked) / seg[i] if seg[i] else 0.0
        (x0, y0), (x1, y1) = loop[i], loop[i + 1]
        out.append((x0 + (x1 - x0) * t, y0 + (y1 - y0) * t))
    return out


class Track:
    def __init__(self, spec: TrackSpec, width: float, height: float) -> None:
        """Fit the track into a width x height area (world coordinates = that area's pixels)."""
        self.spec = spec
        self.name = spec.name
        scale = min(width / DESIGN_W, height / DESIGN_H)
        ox, oy = (width - DESIGN_W * scale) / 2, (height - DESIGN_H * scale) / 2
        controls = tuple((ox + x * scale, oy + y * scale) for x, y in spec.points)
        self.half_width = spec.half_width * scale

        rough = _resample_closed(_catmull_rom_closed(controls), SPACING)
        self.center = _resample_closed(_smooth_closed(rough, radius=3, passes=4), SPACING)
        self.n = len(self.center)
        self.length = self.n * SPACING
        self.tangents: list[Point] = []
        self.normals: list[Point] = []   # pointing to the LEFT of the driving direction
        for i in range(self.n):
            (x0, y0), (x1, y1) = self.center[i - 1], self.center[(i + 1) % self.n]
            d = math.hypot(x1 - x0, y1 - y0) or 1.0
            tx, ty = (x1 - x0) / d, (y1 - y0) / d
            self.tangents.append((tx, ty))
            self.normals.append((ty, -tx))
        hw = self.half_width
        self.left = [(x + nx * hw, y + ny * hw) for (x, y), (nx, ny) in zip(self.center, self.normals)]
        self.right = [(x - nx * hw, y - ny * hw) for (x, y), (nx, ny) in zip(self.center, self.normals)]

    def nearest_index(self, x: float, y: float, hint: int | None = None, window: int = 20) -> int:
        """Closest centerline sample. With a hint, only searches around it (fast, local)."""
        indices = range(self.n) if hint is None else (
            (hint + d) % self.n for d in range(-window, window + 1))
        return min(indices, key=lambda i: (self.center[i][0] - x) ** 2 + (self.center[i][1] - y) ** 2)

    def wall_segments(self, index: int, window: int) -> list[tuple[Point, Point]]:
        """Wall segments of both sides around a centerline index."""
        segs = []
        for d in range(-window, window):
            i, j = (index + d) % self.n, (index + d + 1) % self.n
            segs.append((self.left[i], self.left[j]))
            segs.append((self.right[i], self.right[j]))
        return segs

    def curvature(self, i: int) -> float:
        """Turn angle (radians) between neighbouring samples: big = tight curve."""
        (ax, ay), (bx, by) = self.tangents[i - 1], self.tangents[(i + 1) % self.n]
        return abs(math.atan2(ax * by - ay * bx, ax * bx + ay * by))
