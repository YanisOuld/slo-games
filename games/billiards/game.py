"""8-ball rules on top of the physics. No pygame.

  - Open table until someone legally pots a ball: they get that group
    (solids 1-7 or stripes 9-15), the opponent the other one.
  - You keep shooting while you legally pot one of your balls.
  - Fouls give the opponent the cue ball "in hand" (place it anywhere):
    potting the cue ball, touching nothing, or hitting the wrong ball first.
  - Pot the 8 once your group is cleared to win; pot it early (or with a foul): you lose.
  - The 8 potted on the break is put back on the foot spot.
"""
from __future__ import annotations

import logging
import random

from . import physics
from .models import Group, Phase, Player, ShotOutcome
from .physics import Table

log = logging.getLogger(__name__)

_NAMES = {0: "blanche", 8: "noire"}


def ball_name(number: int) -> str:
    return _NAMES.get(number, str(number))


class Gameplay:
    def __init__(self, names: tuple[str, str] = ("Joueur 1", "Joueur 2"), seed: int | None = None) -> None:
        self.rng = random.Random(seed)
        self.names = names
        self.reset(starter=0)

    def reset(self, starter: int = 0) -> None:
        self.table = Table()
        order = [n for n in range(1, 16) if n != 8]
        self.rng.shuffle(order)
        order.insert(4, 8)   # the black sits in the middle of the rack
        self.table.rack(order)
        self.players = [Player(self.names[0]), Player(self.names[1])]
        self.current = starter
        self.phase = Phase.AIMING
        self.ball_in_hand = False
        self.is_break = True
        self.winner: int | None = None
        self.shots = 0
        self.shot_targets: list[int] = []
        self.last_outcome = ShotOutcome("Casse !", "info")

    # -- queries -----------------------------------------------------------------------

    @property
    def shooter(self) -> Player:
        return self.players[self.current]

    def remaining(self, group: Group | None) -> list[int]:
        if group is None:
            return []
        return [n for n in group.numbers() if not self.table.ball(n).pocketed]

    def legal_targets(self, player: int | None = None) -> list[int]:
        """Balls this player may hit first."""
        p = self.players[self.current if player is None else player]
        if p.group is None:
            return [n for n in range(1, 16) if n != 8 and not self.table.ball(n).pocketed] or [8]
        return self.remaining(p.group) or [8]

    # -- actions -----------------------------------------------------------------------

    def place_cue(self, x: float, y: float) -> bool:
        if not self.ball_in_hand or self.phase is not Phase.AIMING or not self.table.can_place_cue(x, y):
            return False
        cue = self.table.cue
        cue.x, cue.y, cue.pocketed = x, y, False
        return True

    def shoot(self, angle: float, power: float) -> bool:
        if self.phase is not Phase.AIMING or power <= 0:
            return False
        self.shot_targets = self.legal_targets()   # fixed now: balls may drop during the shot
        self.table.strike(angle, power)
        self.phase = Phase.ROLLING
        self.shots += 1
        return True

    def update(self, dt: float) -> bool:
        """Advance the physics by dt (in fixed substeps). Returns True when a shot just ended."""
        if self.phase is not Phase.ROLLING:
            return False
        for _ in range(max(1, round(dt / physics.SUBSTEP))):
            self.table.step()
        if self.table.all_stopped():
            self._end_shot()
            return True
        return False

    # -- rules -------------------------------------------------------------------------

    def _end_shot(self) -> None:
        ev = self.table.events
        me = self.shooter
        targets_before = self.shot_targets
        potted = ev.potted
        foul = None
        if 0 in potted:
            foul = "la blanche est tombée"
        elif ev.first_hit is None:
            foul = "aucune bille touchée"
        elif ev.first_hit not in targets_before and not (self.is_break and ev.first_hit != 0):
            foul = f"la {ball_name(ev.first_hit)} touchée en premier"

        if 8 in potted:
            if self.is_break:
                self._respot(8)
            else:
                cleared = me.group is not None and targets_before == [8]
                self._finish(self.current if cleared and foul is None else 1 - self.current,
                             "noire empochée trop tôt" if not cleared else foul)
                return

        assigned = False
        if me.group is None and foul is None:   # open table: first legal pot decides groups
            first = next((n for n in potted if Group.of(n) is not None), None)
            if first is not None:
                me.group = Group.of(first)
                self.players[1 - self.current].group = me.group.other()
                assigned = True

        own = [n for n in potted if me.group is not None and Group.of(n) is me.group]
        if 0 in potted:
            self._respot_cue()
        self.is_break = False
        self.phase = Phase.AIMING
        names = ", ".join(ball_name(n) for n in potted if n != 0)
        if foul is not None:
            self.current = 1 - self.current
            self.ball_in_hand = True
            self.last_outcome = ShotOutcome(f"Faute : {foul}", "error")
        elif own:
            self.ball_in_hand = False
            group = f" · {me.name} : {me.group.value.lower()}" if assigned else ""
            self.last_outcome = ShotOutcome(f"Empoché : {names}{group} · Rejoue !", "success")
        else:
            self.current = 1 - self.current
            self.ball_in_hand = False
            self.last_outcome = ShotOutcome(f"Empoché : {names}" if names else "Rien d'empoché", "info")

    def _finish(self, winner: int, reason: str | None) -> None:
        self.winner = winner
        self.phase = Phase.OVER
        if winner == self.current:
            self.last_outcome = ShotOutcome(f"{self.players[winner].name} gagne !", "success")
        else:
            self.last_outcome = ShotOutcome(f"Perdu : {reason}", "error")
        log.info("game over: %s wins (%s)", self.players[winner].name, reason or "8 potted")

    def _respot(self, number: int) -> None:
        """Put a ball back on its spot, or just beside it if that's taken."""
        ball = self.table.ball(number)
        x, y = physics.HEAD_SPOT if number == 0 else physics.FOOT_SPOT
        step = (-1 if number == 0 else 1) * (2 * physics.R + 1)
        while not self._free(x, y, ball):
            x += step
        ball.x, ball.y, ball.pocketed, ball.vx, ball.vy = x, y, False, 0.0, 0.0

    def _respot_cue(self) -> None:
        self._respot(0)

    def _free(self, x: float, y: float, ball) -> bool:
        return all(b is ball or b.pocketed or (b.x - x) ** 2 + (b.y - y) ** 2 >= (2 * physics.R + 1) ** 2
                   for b in self.table.balls)
