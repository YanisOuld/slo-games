"""Racing rules. No pygame. World = pixels of the track view, y grows downward.

One call to step() advances exactly STEP_DT seconds, so races can be simulated
faster than real time (e.g. many cars learning at once, later).

Car model (top-down arcade): the velocity lives in the world and is split each step
into a forward part (engine, brakes, drag) and a sideways part that tyre grip damps
out. Low grip (handbrake) lets the sideways part survive: the car drifts.

Lap counting: the car's position is projected on the track's centerline, and the
forward distance travelled along it is accumulated. A lap is one full track length
of forward progress, so driving backwards or cutting can't count laps.
"""
from __future__ import annotations

import logging
import math

from . import constants as k
from .models import Car, Controls, GhostFrame, LapRecord, Sensor, Statistics
from .tracks import Track

log = logging.getLogger(__name__)

_START_BACK = 3  # samples behind the start line where the car is placed


def _clamp(v: float, lo: float = -1.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, v))


class Gameplay:
    def __init__(self, track: Track, best: LapRecord | None = None) -> None:
        self.track = track
        self.best = best  # fastest lap ever on this track (survives restarts)
        self.reset()

    def reset(self) -> None:
        t = self.track
        i = (t.n - _START_BACK) % t.n
        (x, y), (tx, ty) = t.center[i], t.tangents[i]
        self.car = Car(x, y, math.atan2(ty, tx))
        self.index = i                    # nearest centerline sample
        self.progress = -_START_BACK      # samples travelled forward since the start line
        self.time = 0.0
        self.lap_start = 0.0
        self.lap_times: list[float] = []
        self.frames: list[GhostFrame] = []  # current lap, for the ghost
        self.finished = False
        self.new_best = False             # did the last completed lap set the record?
        self.wall_hits = 0
        self.touching_wall = False
        self.drifting = False
        log.info("new race on %s", t.name)

    # -- public API --------------------------------------------------------------------

    @property
    def lap(self) -> int:
        return min(len(self.lap_times) + 1, k.LAPS)

    @property
    def speed(self) -> float:
        return math.hypot(self.car.vx, self.car.vy)

    def statistics(self) -> Statistics:
        return Statistics(self.lap, k.LAPS, self.time - self.lap_start, self.time,
                          self.best.time if self.best else None, self.speed)

    def ghost_frame(self) -> GhostFrame | None:
        """Where the record lap was at this same moment of the lap."""
        if self.best is None or not self.best.frames:
            return None
        return self.best.frames[min(len(self.frames), len(self.best.frames) - 1)]

    def step(self, controls: Controls) -> None:
        if self.finished:
            return
        dt = k.STEP_DT
        self.time += dt
        self._drive(controls, dt)
        self._collide()
        self._advance_progress()
        self.frames.append((self.car.x, self.car.y, self.car.angle))

    def sensors(self) -> list[Sensor]:
        """Distance to the walls along a fan of rays (what a learning driver would 'see')."""
        car = self.car
        segments = self.track.wall_segments(self.index, k.SENSOR_WINDOW)
        out = []
        for deg in k.SENSOR_ANGLES:
            rel = math.radians(deg)
            dx, dy = math.cos(car.angle + rel), math.sin(car.angle + rel)
            best = k.SENSOR_RANGE
            for (ax, ay), (bx, by) in segments:
                hit = _ray_hit(car.x, car.y, dx, dy, ax, ay, bx, by)
                if hit is not None and hit < best:
                    best = hit
            out.append(Sensor(rel, best, car.x + dx * best, car.y + dy * best))
        return out

    # -- physics -----------------------------------------------------------------------

    def _drive(self, c: Controls, dt: float) -> None:
        car = self.car
        fx, fy = math.cos(car.angle), math.sin(car.angle)
        rx, ry = -fy, fx
        forward = car.vx * fx + car.vy * fy
        side = car.vx * rx + car.vy * ry

        throttle = _clamp(c.throttle)
        if throttle > 0:
            forward += k.ENGINE * throttle * dt
        elif throttle < 0:
            if forward > 1:   # moving forward: brake
                forward = max(0.0, forward + k.BRAKE * throttle * dt)
            else:             # stopped or reversing: reverse gear
                forward = max(-k.MAX_REVERSE, forward + k.REVERSE * throttle * dt)
        else:                 # coasting: rolling resistance
            forward -= math.copysign(min(abs(forward), k.ROLLING * dt), forward)
        forward -= forward * k.DRAG * dt

        grip = k.HANDBRAKE_GRIP if c.handbrake else k.GRIP
        side *= math.exp(-grip * dt)
        if c.handbrake:
            forward *= math.exp(-k.HANDBRAKE_DRAG * dt)
        self.drifting = abs(side) > k.DRIFT_SPEED

        car.vx, car.vy = forward * fx + side * rx, forward * fy + side * ry
        # Steering bites with speed (and flips when reversing, like a real car).
        car.angle += _clamp(c.steer) * k.STEER_RATE * _clamp(forward / k.STEER_FULL_SPEED) * dt
        car.x += car.vx * dt
        car.y += car.vy * dt

    def _collide(self) -> None:
        """Car = circle; walls = segments near the car. Push out, bounce a little, scrape."""
        car = self.car
        r = k.CAR_RADIUS
        touching = False
        for (ax, ay), (bx, by) in self.track.wall_segments(self.index, k.COLLISION_WINDOW):
            dx, dy = bx - ax, by - ay
            t = _clamp(((car.x - ax) * dx + (car.y - ay) * dy) / ((dx * dx + dy * dy) or 1.0), 0.0, 1.0)
            ox, oy = car.x - (ax + t * dx), car.y - (ay + t * dy)
            dist = math.hypot(ox, oy)
            if dist >= r or dist == 0:
                continue
            touching = True
            nx, ny = ox / dist, oy / dist
            car.x += nx * (r - dist)
            car.y += ny * (r - dist)
            into = car.vx * nx + car.vy * ny
            if into < 0:
                tx, ty = car.vx - into * nx, car.vy - into * ny   # along the wall
                bounce = -into * k.WALL_BOUNCE
                car.vx = tx * k.WALL_SCRAPE + bounce * nx
                car.vy = ty * k.WALL_SCRAPE + bounce * ny
        if touching and not self.touching_wall:
            self.wall_hits += 1
        self.touching_wall = touching

    # -- laps --------------------------------------------------------------------------

    def _advance_progress(self) -> None:
        n = self.track.n
        new = self.track.nearest_index(self.car.x, self.car.y, hint=self.index, window=6)
        delta = new - self.index
        if delta > n // 2:
            delta -= n
        elif delta < -n // 2:
            delta += n
        self.progress += delta
        self.index = new
        if self.progress >= (len(self.lap_times) + 1) * n:
            self._complete_lap()

    def _complete_lap(self) -> None:
        lap_time = self.time - self.lap_start
        self.new_best = self.best is None or lap_time < self.best.time
        if self.new_best:
            self.best = LapRecord(lap_time, self.frames)
        self.lap_times.append(lap_time)
        log.info("lap %d: %.2fs%s", len(self.lap_times), lap_time, " (record)" if self.new_best else "")
        self.lap_start = self.time
        self.frames = []
        if len(self.lap_times) >= k.LAPS:
            self.finished = True


def _ray_hit(ox: float, oy: float, dx: float, dy: float,
             ax: float, ay: float, bx: float, by: float) -> float | None:
    """Distance along the unit ray (ox,oy)+t(dx,dy) to segment AB, or None."""
    ex, ey = bx - ax, by - ay
    den = dx * ey - dy * ex
    if abs(den) < 1e-9:
        return None
    wx, wy = ax - ox, ay - oy
    t = (wx * ey - wy * ex) / den
    u = (wx * dy - wy * dx) / den
    return t if t >= 0 and 0 <= u <= 1 else None
