"""Pure Runner data types. No pygame here: data and rules, not rendering."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Action(Enum):
    # What the player is holding this step. A human and a future AI agent both
    # drive the game through this, one action per physics step.
    NONE = 0
    JUMP = 1   # held: jumps when grounded, longer hold = higher jump
    DUCK = 2   # on the ground: crouch; in the air: fall faster


class ObstacleKind(Enum):
    BLOCK = "block"            # sits on the ground: jump over it
    DRONE = "drone"            # flies at head height: duck under it (or jump over)
    WAVE_DRONE = "wave drone"  # bobs up and down: time your pass
    SLIME = "slime"            # crawls toward you: jump over it, or stomp it from above
    CEILING = "ceiling"        # hanging spikes: only a short hop fits underneath
    MISSILE = "missile"        # announced by a warning, flies in fast at feet or head height


@dataclass
class Box:
    x: float
    y: float  # top
    w: float
    h: float

    @property
    def right(self) -> float:
        return self.x + self.w

    @property
    def bottom(self) -> float:
        return self.y + self.h

    def intersects(self, other: "Box") -> bool:
        return (self.x < other.right and other.x < self.right
                and self.y < other.bottom and other.y < self.bottom)

    def shrunk(self, margin: float) -> "Box":
        return Box(self.x + margin, self.y + margin, self.w - 2 * margin, self.h - 2 * margin)


@dataclass
class Player:
    x: float          # left edge, world coordinates
    feet: float       # bottom edge: stays put when ducking changes the height
    w: float
    h: float
    vy: float = 0.0
    on_ground: bool = True
    ducking: bool = False
    coyote: float = 0.0

    @property
    def box(self) -> Box:
        return Box(self.x, self.feet - self.h, self.w, self.h)


@dataclass
class Segment:
    """A horizontal walkable surface from x0 to x1 at height y (ground or platform)."""

    x0: float
    x1: float
    y: float


@dataclass
class Obstacle:
    kind: ObstacleKind
    box: Box
    vx: float = 0.0        # world speed (slimes, missiles move left)
    phase: float = 0.0     # wave drones: where they start in their up/down cycle
    stomped: bool = False  # slimes: squashed, harmless, just drawn flat


@dataclass
class MissileWarning:
    bottom: float      # lane of the incoming missile (bottom edge, world y)
    time_left: float   # seconds before it launches


@dataclass
class Coin:
    x: float  # center
    y: float
    taken: bool = False


@dataclass
class Statistics:
    score: int
    meters: int
    coins: int
    stomps: int
    best: int
    speed: float
    zone: int
