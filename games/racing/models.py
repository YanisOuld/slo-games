"""Pure racing data types. No pygame here: data and rules, not rendering."""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Controls:
    """What the driver does this step. Continuous, so a human (keys = -1/0/1)
    and a future learning driver (any value in between) use the same interface."""

    throttle: float = 0.0   # -1 (brake / reverse) .. 1 (full gas)
    steer: float = 0.0      # -1 (left) .. 1 (right)
    handbrake: bool = False


@dataclass
class Car:
    x: float
    y: float
    angle: float            # radians, 0 = facing +x, grows clockwise on screen (y down)
    vx: float = 0.0
    vy: float = 0.0


@dataclass
class Sensor:
    """One distance ray from the car to the nearest wall."""

    angle: float      # relative to the car's heading, radians
    distance: float   # px, capped at the ray length
    hit_x: float
    hit_y: float


GhostFrame = tuple[float, float, float]  # x, y, angle


@dataclass
class LapRecord:
    time: float
    frames: list[GhostFrame] = field(default_factory=list)  # one per physics step


@dataclass
class Statistics:
    lap: int            # current lap, from 1
    laps: int
    lap_time: float
    total_time: float
    best_lap: float | None
    speed: float        # px/s
