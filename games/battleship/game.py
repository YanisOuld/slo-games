"""Battleship rules. No pygame.

Two boards: the player's and the AI's. Ships may touch but not overlap. Players
alternate single shots; hitting a whole ship sinks it, and sinking is announced.
"""
from __future__ import annotations

import logging
import random

from .models import (FLEET, SIZE, CellState, Phase, Shot, ShotResult, Ship, SideStats,
                     TargetView, cells_of)

log = logging.getLogger(__name__)


class Board:
    def __init__(self) -> None:
        self.ships = [Ship(name, size) for name, size in FLEET]
        self.shots: dict[tuple[int, int], Shot] = {}

    # -- placement -----------------------------------------------------------------

    def ship_at(self, x: int, y: int) -> int | None:
        for i, ship in enumerate(self.ships):
            if ship.placed and (x, y) in ship.cells():
                return i
        return None

    def can_place(self, index: int, x: int, y: int, horizontal: bool) -> bool:
        cells = cells_of(x, y, self.ships[index].size, horizontal)
        if not all(0 <= cx < SIZE and 0 <= cy < SIZE for cx, cy in cells):
            return False
        taken = {c for i, s in enumerate(self.ships) if i != index and s.placed for c in s.cells()}
        return not taken.intersection(cells)

    def place(self, index: int, x: int, y: int, horizontal: bool) -> bool:
        if not self.can_place(index, x, y, horizontal):
            return False
        ship = self.ships[index]
        ship.x, ship.y, ship.horizontal = x, y, horizontal
        return True

    def remove(self, index: int) -> None:
        self.ships[index].x = self.ships[index].y = -1

    def randomize(self, rng: random.Random) -> None:
        for i in range(len(self.ships)):
            self.remove(i)
        for i in range(len(self.ships)):
            while not self.place(i, rng.randrange(SIZE), rng.randrange(SIZE), rng.random() < 0.5):
                pass

    @property
    def all_placed(self) -> bool:
        return all(s.placed for s in self.ships)

    def clear_shots(self) -> None:
        self.shots.clear()
        for ship in self.ships:
            ship.hits.clear()

    # -- battle --------------------------------------------------------------------

    def fire(self, x: int, y: int) -> Shot:
        index = self.ship_at(x, y)
        if index is None:
            shot = Shot(x, y, ShotResult.MISS)
        else:
            ship = self.ships[index]
            ship.hits.add((x, y))
            shot = Shot(x, y, ShotResult.SUNK if ship.sunk else ShotResult.HIT, index)
        self.shots[(x, y)] = shot
        return shot

    @property
    def all_sunk(self) -> bool:
        return all(s.sunk for s in self.ships)

    def view(self) -> TargetView:
        """What the opponent knows about this board."""
        states = [[CellState.UNKNOWN] * SIZE for _ in range(SIZE)]
        for (x, y), shot in self.shots.items():
            states[x][y] = CellState.MISS if shot.result is ShotResult.MISS else CellState.HIT
        for ship in self.ships:
            if ship.sunk:
                for x, y in ship.cells():
                    states[x][y] = CellState.SUNK
        return TargetView(states, [s.size for s in self.ships if not s.sunk])


class Gameplay:
    def __init__(self, seed: int | None = None) -> None:
        self.rng = random.Random(seed)
        self.player = Board()   # the human's fleet (the AI shoots here)
        self.enemy = Board()    # the AI's fleet (the human shoots here)
        self.player.randomize(self.rng)
        self.new_game()

    def new_game(self) -> None:
        """Back to placement. The player keeps their last layout as a starting point."""
        self.player.clear_shots()
        self.enemy = Board()
        self.phase = Phase.PLACEMENT
        self.player_turn = True
        self.winner_is_player: bool | None = None
        self.stats = {"player": SideStats(), "ai": SideStats()}

    def start_battle(self) -> bool:
        if not self.player.all_placed:
            return False
        self.enemy.randomize(self.rng)
        self.phase = Phase.BATTLE
        self.player_turn = True
        log.info("battle starts")
        return True

    def player_fire(self, x: int, y: int) -> Shot | None:
        if self.phase is not Phase.BATTLE or not self.player_turn or (x, y) in self.enemy.shots:
            return None
        return self._fire(self.enemy, self.stats["player"], x, y, player=True)

    def ai_fire(self, x: int, y: int) -> Shot | None:
        if self.phase is not Phase.BATTLE or self.player_turn or (x, y) in self.player.shots:
            return None
        return self._fire(self.player, self.stats["ai"], x, y, player=False)

    def _fire(self, board: Board, stats: SideStats, x: int, y: int, player: bool) -> Shot:
        shot = board.fire(x, y)
        stats.shots += 1
        if shot.result is not ShotResult.MISS:
            stats.hits += 1
        if board.all_sunk:
            self.phase = Phase.OVER
            self.winner_is_player = player
            log.info("game over: %s wins in %d shots", "player" if player else "AI", stats.shots)
        else:
            self.player_turn = not player
        return shot
