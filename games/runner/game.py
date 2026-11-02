"""Runner rules. No pygame. World x grows to the right, y grows downward.

The player runs right on its own at an ever-increasing speed; the world is
generated in chunks ahead of it and dropped behind it. One call to step() advances
exactly STEP_DT seconds, so the game can be driven faster than real time.

Zones get exponentially longer (see zone_at_meters). They unlock enemies one at a time
(each shows up more often in the zone that introduces it), then mix them in combos.
"""
from __future__ import annotations

import logging
import math
import random

from engine import constants as screen

from . import constants as k
from .models import (Action, Box, Coin, MissileWarning, Obstacle, ObstacleKind, Player,
                     Segment, Statistics)

log = logging.getLogger(__name__)

# Time a full jump spends in the air; sizes gaps so they're always clearable.
_AIR_TIME = 2 * k.JUMP_VELOCITY / k.GRAVITY

# feature -> (zone that unlocks it, base weight in the random pick)
_FEATURES = {
    "block": (1, 3.0),
    "gap": (1, 2.5),
    "platform": (1, 2.0),
    "drone": (2, 2.0),
    "slime": (3, 2.0),
    "wave_drone": (4, 2.0),
    "ceiling": (5, 1.5),
    "missile": (6, 1.5),
}
_NEW_FEATURE_BOOST = 2.5   # a feature is this much more likely in the zone that introduces it
_COMBO_FROM_ZONE = 3
_COMBO_PARTS = ("block", "drone", "gap", "slime", "wave_drone")


def zone_at_meters(meters: float) -> int:
    """Zone number (from 1) at a given distance; each zone is longer than the last."""
    zone, end, length = 1, k.ZONE_FIRST_LENGTH_M, k.ZONE_FIRST_LENGTH_M
    while meters >= end:
        zone += 1
        length *= k.ZONE_GROWTH
        end += length
    return zone


class Gameplay:
    def __init__(self, seed: int | None = None) -> None:
        self.best = 0  # survives across restarts within a scene
        self.reset(seed)

    def reset(self, seed: int | None = None) -> None:
        self.rng = random.Random(seed)
        self.player = Player(k.PLAYER_SCREEN_X, k.GROUND_Y, k.PLAYER_W, k.PLAYER_H)
        self.speed = float(k.START_SPEED)
        self.distance = 0.0
        self.coins = 0
        self.stomps = 0
        self.time = 0.0
        self.game_over = False
        self.ground: list[Segment] = []
        self.platforms: list[Segment] = []
        self.obstacles: list[Obstacle] = []
        self.coin_list: list[Coin] = []
        self.missile_triggers: list[tuple[float, float]] = []  # (world x, lane bottom)
        self.warnings: list[MissileWarning] = []
        # A long safe stretch at the start so the player can get going.
        self.gen_x = 0.0
        self._add_ground(0, screen.SCREEN_WIDTH)
        self._extend_world()
        log.info("new run")

    # -- public API used by the Scene ---------------------------------------------

    @property
    def camera_x(self) -> float:
        return self.player.x - k.PLAYER_SCREEN_X

    @property
    def meters(self) -> int:
        return int(self.distance / k.PX_PER_METER)

    @property
    def zone(self) -> int:
        return zone_at_meters(self.meters)

    @property
    def score(self) -> int:
        return self.meters + self.coins * k.COIN_POINTS + self.stomps * k.STOMP_POINTS

    def statistics(self) -> Statistics:
        return Statistics(self.score, self.meters, self.coins, self.stomps,
                          self.best, self.speed, self.zone)

    def step(self, action: Action) -> None:
        if self.game_over:
            return
        dt = k.STEP_DT
        p = self.player
        self.time += dt
        self.speed = min(k.MAX_SPEED, self.speed + k.ACCELERATION * dt)

        self._update_duck(action == Action.DUCK)
        if action == Action.JUMP and (p.on_ground or p.coyote > 0):
            p.vy = -k.JUMP_VELOCITY
            p.on_ground = False
            p.coyote = 0.0
            p.ducking = False
            p.h = k.PLAYER_H

        gravity = k.GRAVITY
        if p.vy < 0 and action != Action.JUMP:
            gravity *= k.JUMP_CUT_GRAVITY      # released early: short hop
        if not p.on_ground and action == Action.DUCK:
            gravity *= k.FAST_FALL_GRAVITY

        prev_feet = p.feet
        p.vy += gravity * dt
        p.feet += p.vy * dt
        p.x += self.speed * dt
        self.distance += self.speed * dt

        self._land(prev_feet)
        p.coyote = k.COYOTE_TIME if p.on_ground else max(0.0, p.coyote - dt)
        self._update_enemies(dt)
        self._update_missiles(dt)
        self._check_death(prev_feet)
        self._collect_coins()
        self._extend_world()
        self._cleanup()

    # -- physics -------------------------------------------------------------------

    def _update_duck(self, wants_duck: bool) -> None:
        p = self.player
        p.ducking = wants_duck and p.on_ground
        p.h = k.PLAYER_DUCK_H if p.ducking else k.PLAYER_H

    def _land(self, prev_feet: float) -> None:
        """One-way surfaces: you land on them from above, and pass through from below."""
        p = self.player
        p.on_ground = False
        if p.vy < 0:
            return
        for seg in (*self.ground, *self.platforms):
            if prev_feet <= seg.y <= p.feet and p.x < seg.x1 and seg.x0 < p.x + p.w:
                p.feet = seg.y
                p.vy = 0.0
                p.on_ground = True
                return

    def _check_death(self, prev_feet: float) -> None:
        p = self.player
        box = p.box
        if box.y > screen.SCREEN_HEIGHT:
            self._die("fell")
            return
        # Below ground level and touching a ground segment = slammed into a pit wall.
        if p.feet > k.GROUND_Y + 2 and any(p.x < g.x1 and g.x0 < box.right for g in self.ground):
            self._die("pit wall")
            return
        hitbox = box.shrunk(k.HITBOX_MARGIN)
        for ob in self.obstacles:
            if ob.stomped or not hitbox.intersects(ob.box):
                continue
            if (ob.kind is ObstacleKind.SLIME and p.vy > 0
                    and prev_feet <= ob.box.y + k.STOMP_TOLERANCE):
                self._stomp(ob)
                continue
            self._die(ob.kind.value)
            return

    def _stomp(self, slime: Obstacle) -> None:
        slime.stomped = True
        slime.vx = 0.0
        self.stomps += 1
        self.player.vy = -k.STOMP_BOUNCE
        self.player.on_ground = False

    def _die(self, cause: str) -> None:
        self.game_over = True
        self.best = max(self.best, self.score)
        log.info("game over (%s): score=%d, %dm, zone %d", cause, self.score, self.meters, self.zone)

    def _collect_coins(self) -> None:
        box = self.player.box
        r = k.COIN_RADIUS
        for coin in self.coin_list:
            if not coin.taken and box.intersects(Box(coin.x - r, coin.y - r, 2 * r, 2 * r)):
                coin.taken = True
                self.coins += 1

    # -- enemies -------------------------------------------------------------------

    def _update_enemies(self, dt: float) -> None:
        screen_right = self.camera_x + screen.SCREEN_WIDTH
        for ob in self.obstacles:
            if ob.kind is ObstacleKind.WAVE_DRONE:
                ob.box.y = self._wave_top(ob)
            elif ob.kind is ObstacleKind.SLIME and ob.vx and ob.box.x < screen_right:
                # Slimes only start crawling once on screen, and stop at edges and blocks.
                moved = Box(ob.box.x + ob.vx * dt, ob.box.y, ob.box.w, ob.box.h)
                if self._slime_can_go(moved):
                    ob.box = moved
                else:
                    ob.vx = 0.0
            elif ob.kind is ObstacleKind.MISSILE:
                ob.box.x += ob.vx * dt

    def _wave_top(self, ob: Obstacle) -> float:
        bottom = k.GROUND_Y - k.WAVE_CENTER - k.WAVE_AMPLITUDE * math.sin(
            ob.phase + self.time * k.WAVE_FREQUENCY)
        return bottom - ob.box.h

    def _slime_can_go(self, box: Box) -> bool:
        on_ground = any(g.x0 <= box.x and box.right <= g.x1 for g in self.ground)
        blocked = any(o.kind is ObstacleKind.BLOCK and o.box.intersects(box) for o in self.obstacles)
        return on_ground and not blocked

    def _update_missiles(self, dt: float) -> None:
        for trigger in [t for t in self.missile_triggers if self.player.x >= t[0]]:
            self.missile_triggers.remove(trigger)
            self.warnings.append(MissileWarning(trigger[1], k.MISSILE_WARNING))
        for warning in list(self.warnings):
            warning.time_left -= dt
            if warning.time_left <= 0:
                self.warnings.remove(warning)
                x = self.camera_x + screen.SCREEN_WIDTH + 10
                box = Box(x, warning.bottom - k.MISSILE_H, k.MISSILE_W, k.MISSILE_H)
                self.obstacles.append(Obstacle(ObstacleKind.MISSILE, box, vx=-k.MISSILE_SPEED))

    # -- world generation ----------------------------------------------------------

    def _zone_at(self, x: float) -> int:
        return zone_at_meters((x - k.PLAYER_SCREEN_X) / k.PX_PER_METER)

    def _unlocked(self, names: tuple[str, ...] | None = None) -> list[str]:
        zone = self._zone_at(self.gen_x)
        return [f for f in (names or _FEATURES) if _FEATURES[f][0] <= zone]

    def _extend_world(self) -> None:
        while self.gen_x < self.player.x + k.SPAWN_AHEAD:
            self._add_chunk()

    def _cleanup(self) -> None:
        left = self.camera_x - k.DESPAWN_BEHIND
        self.ground = [g for g in self.ground if g.x1 > left]
        self.platforms = [s for s in self.platforms if s.x1 > left]
        self.obstacles = [o for o in self.obstacles if o.box.right > left]
        self.coin_list = [c for c in self.coin_list if c.x > left and not c.taken]

    def _add_chunk(self) -> None:
        """A chunk = a stretch of flat ground to react on, then one feature."""
        r = self.rng
        x = self.gen_x
        zone = self._zone_at(x)
        names = self._unlocked()
        weights = [
            _FEATURES[f][1] * (_NEW_FEATURE_BOOST if _FEATURES[f][0] == zone > 1 else 1.0)
            for f in names
        ]
        if zone >= _COMBO_FROM_ZONE:
            names.append("combo")
            weights.append(min(4.0, 0.8 * (zone - _COMBO_FROM_ZONE + 1)))
        feature = r.choices(names, weights=weights)[0]

        run = r.uniform(200, 380) + self.speed * 0.5
        self._add_ground(x, x + run)
        if r.random() < 0.35:
            self._coin_row(x + run * 0.3, k.GROUND_Y - 40, 5)
        getattr(self, f"_feature_{feature}")(x + run)

    def _feature_block(self, x: float, max_h: float = 62) -> None:
        r = self.rng
        w = r.choice((32, 44, 70))
        h = r.uniform(min(34, max_h), max_h)
        self.obstacles.append(Obstacle(ObstacleKind.BLOCK, Box(x, k.GROUND_Y - h, w, h)))
        self._coin_arc(x + w / 2, k.GROUND_Y - h - 50)
        self._add_ground(x, x + w)

    def _feature_drone(self, x: float) -> None:
        # Bottom edge between ducking height and standing height: duck or jump.
        bottom = k.GROUND_Y - 34
        box = Box(x, bottom - k.DRONE_H, k.DRONE_W, k.DRONE_H)
        self.obstacles.append(Obstacle(ObstacleKind.DRONE, box))
        self._add_ground(x, x + k.DRONE_W)

    def _feature_wave_drone(self, x: float) -> None:
        ob = Obstacle(ObstacleKind.WAVE_DRONE, Box(x, 0, k.DRONE_W, k.DRONE_H),
                      phase=self.rng.uniform(0, 2 * math.pi))
        ob.box.y = self._wave_top(ob)
        self.obstacles.append(ob)
        self._add_ground(x, x + k.DRONE_W)

    def _feature_slime(self, x: float) -> None:
        box = Box(x, k.GROUND_Y - k.SLIME_H, k.SLIME_W, k.SLIME_H)
        self.obstacles.append(Obstacle(ObstacleKind.SLIME, box, vx=-k.SLIME_SPEED))
        self._coin_arc(x + k.SLIME_W / 2, k.GROUND_Y - 100)
        self._add_ground(x, x + k.SLIME_W)

    def _feature_gap(self, x: float) -> None:
        max_gap = self.speed * _AIR_TIME * 0.6
        gap = self.rng.uniform(90, max(100, max_gap))
        self._coin_arc(x + gap / 2, k.GROUND_Y - 110)
        self.gen_x = x + gap

    def _feature_platform(self, x: float) -> None:
        r = self.rng
        before, after = r.uniform(50, 80), r.uniform(50, 80)
        length = r.uniform(220, 380)
        y = k.GROUND_Y - r.uniform(70, 110)
        self.platforms.append(Segment(x + before, x + before + length, y))
        self._coin_row(x + before + 40, y - 30, int(length // 60))
        self.gen_x = x + before + length + after

    def _feature_ceiling(self, x: float) -> None:
        # Hanging spikes over a low block: hop over it without a full jump.
        r = self.rng
        length = r.uniform(280, 420)
        bottom = k.GROUND_Y - k.CEILING_CLEARANCE
        self.obstacles.append(Obstacle(ObstacleKind.CEILING, Box(x, -40, length, bottom + 40)))
        self._add_ground(x, x + length * 0.5 - 15)
        self._feature_block(self.gen_x, max_h=28)
        self._add_ground(self.gen_x, x + length)

    def _feature_missile(self, x: float) -> None:
        # A long flat stretch: the warning starts as the player reaches x, then the
        # missile crosses the screen. Two missiles in a row from zone 7.
        r = self.rng
        volley = 2 if self._zone_at(x) >= 7 and r.random() < 0.5 else 1
        spacing = self.speed * 0.8
        for i in range(volley):
            lane = r.choice((k.MISSILE_LOW_BOTTOM, k.MISSILE_HIGH_BOTTOM))
            self.missile_triggers.append((x + i * spacing, lane))
        flight = (screen.SCREEN_WIDTH - k.PLAYER_SCREEN_X) / (self.speed + k.MISSILE_SPEED)
        length = self.speed * (k.MISSILE_WARNING + flight) + (volley - 1) * spacing + 300
        self._coin_row(x + 100, k.GROUND_Y - 40, 4)
        self._add_ground(x, x + length)

    def _feature_combo(self, x: float) -> None:
        # Two features close together: land from the first, react to the second.
        r = self.rng
        first = r.choice(self._unlocked(("block", "drone", "slime", "wave_drone")))
        getattr(self, f"_feature_{first}")(x)
        spacing = self.speed * _AIR_TIME + r.uniform(80, 160)
        self._add_ground(self.gen_x, self.gen_x + spacing)
        second = r.choice(self._unlocked(_COMBO_PARTS))
        getattr(self, f"_feature_{second}")(self.gen_x)

    def _add_ground(self, x0: float, x1: float) -> None:
        if self.ground and abs(self.ground[-1].x1 - x0) < 1:
            self.ground[-1].x1 = x1   # merge with the previous segment
        else:
            self.ground.append(Segment(x0, x1, k.GROUND_Y))
        self.gen_x = x1

    def _coin_row(self, x: float, y: float, count: int) -> None:
        self.coin_list.extend(Coin(x + i * 32, y) for i in range(count))

    def _coin_arc(self, cx: float, top: float) -> None:
        self.coin_list.extend(Coin(cx + dx, top + abs(dx) * 0.4) for dx in (-40, 0, 40))
