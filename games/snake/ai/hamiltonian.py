"""Hamiltonian-cycle Snake AI with verified shortcuts.

Backbone: a Hamiltonian cycle that visits every cell exactly once. Following it
blindly never kills the snake (it can't trap itself and it eventually eats every
food) but it is slow. On top of that we take *shortcuts* toward the food, and
every shortcut is verified before it is used:

  1. it must not run into a wall or the body, and
  2. after the move the head must still be able to reach its own tail through free
     cells -- if it always can, it can always follow the tail and stay alive.

So a shortcut is only ever taken when it is provably not a shortcut to death; if a
candidate fails, we fall back to the plain cycle move (the guaranteed route).
"""
from __future__ import annotations

import logging
from collections import deque

from ..game import Gameplay
from ..models import Coord, Direction
from .agent import SnakeAgent

log = logging.getLogger(__name__)

_MOVES = (Direction.UP, Direction.DOWN, Direction.LEFT, Direction.RIGHT)


class HamiltonianAgent(SnakeAgent):
    def __init__(self, width: int, height: int, shortcuts: bool = True) -> None:
        if width % 2 != 0:
            raise ValueError("width (columns) must be even to build the cycle")
        self.width = width
        self.height = height
        self.shortcuts = shortcuts
        self.n = width * height
        self.cycle = self._build_cycle()          # Coord -> index along the cycle
        self.by_index = {i: c for c, i in self.cycle.items()}

    # -- public API ----------------------------------------------------------

    def next_direction(self, game: Gameplay) -> Direction:
        head = game.snake[0]
        # 1) Try a shortcut toward the food, but only if it survives verification.
        if self.shortcuts:
            shortcut = self._shortcut_direction(game)
            if shortcut is not None and self._is_safe(game, shortcut):
                return shortcut
        # 2) Fall back to the Hamiltonian cycle -- the guaranteed-safe route.
        cycle_dir = self._cycle_direction(head)
        if self._is_safe(game, cycle_dir):
            return cycle_dir
        # 3) Last resort: head to the roomiest free neighbour to buy time.
        return self._survival_direction(game) or cycle_dir

    # -- shortcut heuristic --------------------------------------------------

    def _shortcut_direction(self, game: Gameplay) -> Direction | None:
        """Propose the neighbour that jumps as far ahead toward the food as it can
        without overshooting the food or overtaking the tail. Verified by caller."""
        head, tail = game.snake[0], game.snake[-1]
        body = set(game.snake)
        head_i = self.cycle[head]
        dist_food = (self.cycle[game.food] - head_i) % self.n
        dist_tail = (self.cycle[tail] - head_i) % self.n
        best_dir, best_dist = None, 0
        for d in _MOVES:
            if d == game.direction.opposite():
                continue
            nxt = head.moved(d)
            if not self._inside(nxt) or (nxt in body and nxt != tail):
                continue
            dn = (self.cycle[nxt] - head_i) % self.n
            if dn == 0:
                continue
            if dist_tail and dn >= dist_tail:   # would cut in front of the tail
                continue
            if dn > dist_food:                  # would jump past the food
                continue
            if dn > best_dist:
                best_dir, best_dist = d, dn
        return best_dir

    # -- cycle following -----------------------------------------------------

    def _cycle_direction(self, head: Coord) -> Direction:
        nxt = self.by_index[(self.cycle[head] + 1) % self.n]
        return Direction((nxt.x - head.x, nxt.y - head.y))

    # -- safety verification -------------------------------------------------

    def _is_safe(self, game: Gameplay, direction: Direction) -> bool:
        head = game.snake[0]
        new_head = head.moved(direction)
        if not self._inside(new_head):
            return False
        grew = new_head == game.food
        # Cells still occupied after moving (the tail vacates unless we eat).
        remaining = game.snake if grew else game.snake[:-1]
        if new_head in remaining:
            return False
        new_body = [new_head] + remaining
        # Safe iff the new head can still reach its (new) tail through free space.
        return self._can_reach(new_head, new_body[-1], set(new_body))

    def _can_reach(self, start: Coord, target: Coord, obstacles: set[Coord]) -> bool:
        # The tail counts as free: it moves away as the snake advances.
        blocked = obstacles - {target}
        seen, queue = {start}, deque([start])
        while queue:
            cell = queue.popleft()
            if cell == target:
                return True
            for d in _MOVES:
                nb = cell.moved(d)
                if self._inside(nb) and nb not in blocked and nb not in seen:
                    seen.add(nb)
                    queue.append(nb)
        return False

    def _survival_direction(self, game: Gameplay) -> Direction | None:
        head, tail = game.snake[0], game.snake[-1]
        blocked = set(game.snake) - {tail}
        best_dir, best_room = None, -1
        for d in _MOVES:
            if d == game.direction.opposite():
                continue
            nxt = head.moved(d)
            if not self._inside(nxt) or nxt in blocked:
                continue
            room = self._reachable_count(nxt, blocked)
            if room > best_room:
                best_dir, best_room = d, room
        return best_dir

    def _reachable_count(self, start: Coord, blocked: set[Coord]) -> int:
        seen, queue = {start}, deque([start])
        while queue:
            cell = queue.popleft()
            for d in _MOVES:
                nb = cell.moved(d)
                if self._inside(nb) and nb not in blocked and nb not in seen:
                    seen.add(nb)
                    queue.append(nb)
        return len(seen)

    # -- cycle construction --------------------------------------------------

    def _build_cycle(self) -> dict[Coord, int]:
        """Boustrophedon Hamiltonian cycle (requires an even number of columns).

        Column 0 is the down-leg; columns 1..W-1 zig-zag over rows 1..H-1; row 0
        (for x>=1) is the return highway back to (0,0), closing the loop.
        """
        w, h = self.width, self.height
        path: list[Coord] = [Coord(0, y) for y in range(h)]      # column 0, down
        going_up = True
        for x in range(1, w):                                    # zig-zag columns
            rows = range(h - 1, 0, -1) if going_up else range(1, h)
            path.extend(Coord(x, y) for y in rows)
            going_up = not going_up
        path.extend(Coord(x, 0) for x in range(w - 1, 0, -1))    # return highway
        assert len(path) == self.n, (len(path), self.n)
        return {coord: i for i, coord in enumerate(path)}

    # -- helpers -------------------------------------------------------------

    def _inside(self, c: Coord) -> bool:
        return 0 <= c.x < self.width and 0 <= c.y < self.height
