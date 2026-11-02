"""Pool table physics. No pygame: pure math, so the AI can simulate shots too.

Coordinates are local to the playing surface: (0, 0) is the top-left cushion
corner, (W, H) the bottom-right. Balls are equal-mass discs:

  - they slow down by table friction (constant) plus a little drag,
  - ball-ball hits exchange momentum along the line of centers (elastic, slightly lossy),
  - cushions are segments between the pocket mouths; segment ends act as the
    rounded jaws, so a ball can rattle off a pocket's edge,
  - a ball whose center crosses the cushion line (only possible at a mouth) is pocketed.

Physics runs in small fixed substeps, and only moving balls are integrated and
tested, so a table at rest costs nothing (Raspberry Pi friendly).
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

W, H = 560.0, 280.0          # playing surface, 2:1 like a real table
R = 9.0                      # ball radius
CORNER_MOUTH, SIDE_MOUTH = 21.0, 15.0
FRICTION = 230.0             # px/s² rolling resistance
DRAG = 0.35                  # 1/s
BALL_RESTITUTION = 0.95
CUSHION_RESTITUTION = 0.78
STOP_SPEED = 4.0
MAX_SPEED = 1450.0           # cue ball speed at full power
SUBSTEP = 1 / 240

POCKETS = ((0.0, 0.0), (W / 2, 0.0), (W, 0.0), (0.0, H), (W / 2, H), (W, H))
CUSHIONS = (
    ((CORNER_MOUTH, 0.0), (W / 2 - SIDE_MOUTH, 0.0)), ((W / 2 + SIDE_MOUTH, 0.0), (W - CORNER_MOUTH, 0.0)),
    ((CORNER_MOUTH, H), (W / 2 - SIDE_MOUTH, H)), ((W / 2 + SIDE_MOUTH, H), (W - CORNER_MOUTH, H)),
    ((0.0, CORNER_MOUTH), (0.0, H - CORNER_MOUTH)), ((W, CORNER_MOUTH), (W, H - CORNER_MOUTH)),
)
HEAD_SPOT = (W * 0.25, H / 2)
FOOT_SPOT = (W * 0.72, H / 2)


@dataclass
class Ball:
    number: int              # 0 = cue ball, 8 = black, 1-7 solids, 9-15 stripes
    x: float
    y: float
    vx: float = 0.0
    vy: float = 0.0
    pocketed: bool = False

    @property
    def moving(self) -> bool:
        return not self.pocketed and (self.vx or self.vy)


@dataclass
class ShotEvents:
    """What happened during one shot (used by the rules and the AI)."""

    first_hit: int | None = None             # number of the first ball the cue ball touched
    potted: list[int] = field(default_factory=list)
    cushion_hits: int = 0


class Table:
    def __init__(self) -> None:
        self.balls: list[Ball] = []
        self.events = ShotEvents()

    @property
    def cue(self) -> Ball:
        return self.balls[0]

    def ball(self, number: int) -> Ball:
        return next(b for b in self.balls if b.number == number)

    def rack(self, order: list[int]) -> None:
        """Cue ball on the head spot, 15 balls in a triangle at the foot spot."""
        self.balls = [Ball(0, *HEAD_SPOT)]
        fx, fy = FOOT_SPOT
        dx, dy = R * math.sqrt(3) + 0.2, 2 * R + 0.2
        i = 0
        for row in range(5):
            for k in range(row + 1):
                self.balls.append(Ball(order[i], fx + row * dx, fy + (k - row / 2) * dy))
                i += 1

    def copy(self) -> "Table":
        t = Table()
        t.balls = [Ball(b.number, b.x, b.y, b.vx, b.vy, b.pocketed) for b in self.balls]
        return t

    # -- shooting ------------------------------------------------------------------

    def strike(self, angle: float, power: float) -> None:
        speed = MAX_SPEED * max(0.0, min(1.0, power))
        self.cue.vx, self.cue.vy = math.cos(angle) * speed, math.sin(angle) * speed
        self.events = ShotEvents()

    def all_stopped(self) -> bool:
        return not any(b.moving for b in self.balls)

    def can_place_cue(self, x: float, y: float) -> bool:
        if not (R <= x <= W - R and R <= y <= H - R):
            return False
        return all(b.pocketed or b.number == 0 or math.hypot(b.x - x, b.y - y) >= 2 * R + 1 for b in self.balls)

    def simulate(self, max_time: float = 12.0, dt: float = SUBSTEP) -> ShotEvents:
        """Run until every ball rests (AI look-ahead). Returns the shot's events."""
        t = 0.0
        while not self.all_stopped() and t < max_time:
            self.step(dt)
            t += dt
        return self.events

    # -- one physics substep --------------------------------------------------------

    def step(self, dt: float = SUBSTEP) -> None:
        moving = [b for b in self.balls if b.moving]
        if not moving:
            return
        for b in moving:
            b.x += b.vx * dt
            b.y += b.vy * dt
            speed = math.hypot(b.vx, b.vy)
            new = max(0.0, speed - FRICTION * dt - speed * DRAG * dt)
            if new < STOP_SPEED:
                b.vx = b.vy = 0.0
            else:
                b.vx, b.vy = b.vx * new / speed, b.vy * new / speed
        on_table = [b for b in self.balls if not b.pocketed]
        for b in moving:
            for other in on_table:
                if other is not b and (not other.moving or other.number > b.number):
                    self._collide_balls(b, other)
            self._collide_cushions(b)
            if not (0.0 <= b.x <= W and 0.0 <= b.y <= H):
                # Cushions keep centers inside except at the pocket mouths, so a center
                # past the cushion line is in a mouth: it drops (never stuck in the jaws).
                b.pocketed = True
                b.vx = b.vy = 0.0
                self.events.potted.append(b.number)

    def _collide_balls(self, a: Ball, b: Ball) -> None:
        dx, dy = b.x - a.x, b.y - a.y
        dist2 = dx * dx + dy * dy
        if dist2 >= 4 * R * R or dist2 == 0:
            return
        dist = math.sqrt(dist2)
        nx, ny = dx / dist, dy / dist
        overlap = 2 * R - dist
        a.x -= nx * overlap / 2
        a.y -= ny * overlap / 2
        b.x += nx * overlap / 2
        b.y += ny * overlap / 2
        closing = (a.vx - b.vx) * nx + (a.vy - b.vy) * ny
        if closing <= 0:
            return
        impulse = closing * (1 + BALL_RESTITUTION) / 2
        a.vx -= impulse * nx
        a.vy -= impulse * ny
        b.vx += impulse * nx
        b.vy += impulse * ny
        if self.events.first_hit is None and 0 in (a.number, b.number):
            self.events.first_hit = b.number if a.number == 0 else a.number

    def _collide_cushions(self, b: Ball) -> None:
        for (ax, ay), (bx, by) in CUSHIONS:
            sx, sy = bx - ax, by - ay
            t = max(0.0, min(1.0, ((b.x - ax) * sx + (b.y - ay) * sy) / (sx * sx + sy * sy)))
            ox, oy = b.x - (ax + t * sx), b.y - (ay + t * sy)
            dist = math.hypot(ox, oy)
            if dist >= R or dist == 0:
                continue
            nx, ny = ox / dist, oy / dist
            b.x += nx * (R - dist)
            b.y += ny * (R - dist)
            into = b.vx * nx + b.vy * ny
            if into < 0:
                b.vx -= (1 + CUSHION_RESTITUTION) * into * nx
                b.vy -= (1 + CUSHION_RESTITUTION) * into * ny
                self.events.cushion_hits += 1

    # -- aiming guide ------------------------------------------------------------------

    def predict(self, angle: float) -> tuple[tuple[float, float], Ball | None]:
        """Where the cue ball first touches something going straight at `angle`:
        the ghost-ball position, and the ball it hits (None = a cushion)."""
        cue = self.cue
        dx, dy = math.cos(angle), math.sin(angle)
        best_t, hit = math.inf, None
        for b in self.balls:
            if b.pocketed or b.number == 0:
                continue
            # Ray vs circle of radius 2R around b (where centers touch).
            fx, fy = cue.x - b.x, cue.y - b.y
            proj = fx * dx + fy * dy
            disc = proj * proj - (fx * fx + fy * fy - 4 * R * R)
            if disc < 0:
                continue
            t = -proj - math.sqrt(disc)
            if 0 < t < best_t:
                best_t, hit = t, b
        # Cushion lines (inset by R, where the ball's center bounces).
        for t in (((R - cue.x) / dx) if dx < 0 else ((W - R - cue.x) / dx) if dx > 0 else math.inf,
                  ((R - cue.y) / dy) if dy < 0 else ((H - R - cue.y) / dy) if dy > 0 else math.inf):
            if 0 < t < best_t:
                best_t, hit = t, None
        return (cue.x + dx * best_t, cue.y + dy * best_t), hit
