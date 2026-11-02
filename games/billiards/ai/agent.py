"""Billiards AI: geometric shot finding ("ghost ball"), plus simulation on Hard.

To pot ball B into pocket P, the cue ball must touch B at the "ghost ball" spot:
2R behind B on the line P -> B. A shot is possible if the cue ball can travel to
the ghost spot and B can travel to P without hitting other balls, and the cut angle
isn't too thin. Shots are scored by cut angle and distances (easier = higher).

Levels differ by aiming noise, and Hard also replays its best few shots in a copy of
the table to drop those that would foul or scratch. Everything only reads the game:
the Scene applies the chosen shot exactly like a human's.
"""
from __future__ import annotations

import math
import random
import time
from dataclasses import dataclass

from .. import physics
from ..game import Gameplay
from ..models import Level
from ..physics import POCKETS, R, Table

_MAX_CUT = math.radians(72)
_NOISE = {Level.EASY: (2.6, 0.10), Level.MEDIUM: (0.9, 0.05), Level.HARD: (0.3, 0.02)}  # degrees, power
_SIM_BUDGET = 0.6   # seconds of look-ahead simulation (Hard)
_SIM_TRIES = 4      # noisy replays per candidate shot


@dataclass
class PlannedShot:
    angle: float
    power: float
    cue_pos: tuple[float, float] | None = None   # where to put the cue ball (ball in hand)
    target: int | None = None
    score: float = 0.0


class BilliardsAI:
    def __init__(self, level: Level, rng: random.Random | None = None) -> None:
        self.level = level
        self.rng = rng or random.Random()

    def plan(self, game: Gameplay) -> PlannedShot:
        table, targets = game.table, game.legal_targets()
        if game.is_break:   # break: full power into the front ball of the rack
            front = min((b for b in table.balls if b.number), key=lambda b: b.x)
            angle = math.atan2(front.y - table.cue.y, front.x - table.cue.x)
            return PlannedShot(angle + math.radians(self.rng.gauss(0, 0.4)), 1.0)
        cue_pos = self._best_cue_spot(table, targets) if game.ball_in_hand else None
        start = cue_pos or (table.cue.x, table.cue.y)
        shots = sorted(self._candidates(table, start, targets), key=lambda s: -s.score)
        if not shots:
            shot = self._safety(table, start, targets)
        elif self.level is Level.EASY:
            shot = self.rng.choice(shots[:3])
        elif self.level is Level.HARD:
            shot = self._verify(game, shots[:5], cue_pos) or shots[0]
        else:
            shot = shots[0]
        shot.cue_pos = cue_pos
        angle_noise, power_noise = _NOISE[self.level]
        shot.angle += math.radians(self.rng.gauss(0, angle_noise))
        shot.power = min(1.0, max(0.12, shot.power * (1 + self.rng.uniform(-power_noise, power_noise))))
        return shot

    # -- shot finding --------------------------------------------------------------------

    def _candidates(self, table: Table, start: tuple[float, float], targets: list[int]) -> list[PlannedShot]:
        cx, cy = start
        others = [b for b in table.balls if not b.pocketed and b.number != 0]
        shots = []
        for number in targets:
            ball = table.ball(number)
            for px, py in POCKETS:
                dx, dy = px - ball.x, py - ball.y
                d2 = math.hypot(dx, dy)
                if d2 < 1:
                    continue
                ux, uy = dx / d2, dy / d2
                if px == physics.W / 2 and abs(uy) < 0.55:   # side pockets need a straight-ish entry
                    continue
                gx, gy = ball.x - ux * 2 * R, ball.y - uy * 2 * R   # ghost ball
                vx, vy = gx - cx, gy - cy
                d1 = math.hypot(vx, vy)
                if d1 < 1:
                    continue
                cos_cut = (vx * ux + vy * uy) / d1
                if cos_cut < math.cos(_MAX_CUT):
                    continue
                if not (_clear(cx, cy, gx, gy, others, ignore=ball) and _clear(ball.x, ball.y, px, py, others, ignore=ball)):
                    continue
                score = cos_cut ** 3 / (1 + (d1 + d2) / 600)
                shots.append(PlannedShot(math.atan2(vy, vx), _power(d1, d2, cos_cut), target=number, score=score))
        return shots

    def _safety(self, table: Table, start: tuple[float, float], targets: list[int]) -> PlannedShot:
        """No pot in sight: at least touch a legal ball first (avoid giving ball in hand).
        Sweeps directions with the aiming guide's ray test and keeps those whose first
        contact is a legal ball, preferring the nearest (easiest to control)."""
        probe = table.copy()
        probe.cue.x, probe.cue.y = start
        options = []
        for i in range(180):
            angle = i * math.pi / 90
            (gx, gy), hit = probe.predict(angle)
            if hit is not None and hit.number in targets:
                options.append((math.hypot(gx - start[0], gy - start[1]), angle))
        if not options:   # nothing reachable in a straight line: hit something anyway
            ball = table.ball(targets[0])
            return PlannedShot(math.atan2(ball.y - start[1], ball.x - start[0]), 0.45, target=ball.number)
        distance, angle = min(options)
        return PlannedShot(angle, min(0.7, 0.25 + distance / 900))

    def _best_cue_spot(self, table: Table, targets: list[int]) -> tuple[float, float]:
        """Ball in hand: try spots and keep the one giving the easiest shot."""
        best, best_score = (physics.HEAD_SPOT), -1.0
        for _ in range(40):
            x = self.rng.uniform(R * 2, physics.W - R * 2)
            y = self.rng.uniform(R * 2, physics.H - R * 2)
            if not table.can_place_cue(x, y):
                continue
            shots = self._candidates(table, (x, y), targets)
            score = max((s.score for s in shots), default=0.0)
            if score > best_score:
                best, best_score = (x, y), score
        return best

    def _verify(self, game: Gameplay, shots: list[PlannedShot],
                cue_pos: tuple[float, float] | None) -> PlannedShot | None:
        """Hard: replay each of the best shots a few times in a copy of the table, with
        the same small aiming errors the AI really makes, and keep the shot with the
        best AVERAGE outcome. A shot that only works when perfect is a trap: this
        prefers reliable shots over spectacular ones."""
        deadline = time.perf_counter() + _SIM_BUDGET
        targets = game.legal_targets()
        angle_noise, power_noise = _NOISE[self.level]
        best, best_value = None, -math.inf
        for shot in shots:
            if time.perf_counter() > deadline:
                break
            total = 0.0
            for _ in range(_SIM_TRIES):
                table = game.table.copy()
                if cue_pos:
                    table.cue.x, table.cue.y = cue_pos
                table.strike(shot.angle + math.radians(self.rng.gauss(0, angle_noise)),
                             shot.power * (1 + self.rng.uniform(-power_noise, power_noise)))
                total += _outcome_value(table.simulate(), targets)
            value = shot.score + total / _SIM_TRIES
            if value > best_value:
                best, best_value = shot, value
        return best


def _outcome_value(ev, targets: list[int]) -> float:
    value = 0.0
    if 0 in ev.potted or ev.first_hit not in targets:
        value -= 5   # foul: ball in hand for the opponent
    if 8 in ev.potted and targets != [8]:
        value -= 20  # potting the black early loses the game
    return value + 2 * sum(1 for n in ev.potted if n in targets)


def _clear(x0: float, y0: float, x1: float, y1: float, balls, ignore, margin: float = 2 * R) -> bool:
    """No ball (except `ignore`) within `margin` of the segment: the path is free."""
    sx, sy = x1 - x0, y1 - y0
    length2 = sx * sx + sy * sy or 1.0
    for b in balls:
        if b is ignore:
            continue
        t = max(0.0, min(1.0, ((b.x - x0) * sx + (b.y - y0) * sy) / length2))
        if math.hypot(b.x - (x0 + t * sx), b.y - (y0 + t * sy)) < margin:
            return False
    return True


def _distance(v_start: float, v_end: float) -> float:
    """Distance a ball rolls while slowing from v_start to v_end under the table's
    friction F and drag D (dv/dt = -(F + D·v)): integral of v / (F + D·v) dv."""
    f, d = physics.FRICTION, physics.DRAG

    def antiderivative(v: float) -> float:
        return v / d - f / (d * d) * math.log(f + d * v)

    return antiderivative(v_start) - antiderivative(v_end)


def _speed_for(distance: float, v_end: float = 0.0) -> float:
    """Starting speed needed to roll `distance` and still have v_end (bisection)."""
    lo, hi = v_end, physics.MAX_SPEED * 3
    for _ in range(40):
        mid = (lo + hi) / 2
        if _distance(mid, v_end) < distance:
            lo = mid
        else:
            hi = mid
    return hi


def _power(d1: float, d2: float, cos_cut: float) -> float:
    """Enough speed for the object ball to reach the pocket (with margin), and for the
    cue ball to arrive at the ghost spot fast enough to give it that speed."""
    v_object = _speed_for(d2 + 45)
    v_contact = v_object / max(0.25, cos_cut * (1 + physics.BALL_RESTITUTION) / 2)
    v0 = _speed_for(d1, v_contact)
    return min(1.0, max(0.12, v0 / physics.MAX_SPEED))
