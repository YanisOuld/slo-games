"""Logic Minesweeper solver.

It only reads what a human sees: revealed numbers and flags (never cell.mine).
Each revealed number gives a constraint "these hidden cells hold exactly n mines".

  1. Trivial rule: n == 0 -> all safe; n == size -> all mines.
  2. Subset rule: if A is inside B, then B minus A holds n_B - n_A mines, which can
     settle cells that neither constraint settles alone.
  3. A global constraint (all hidden cells hold the remaining mines) helps the endgame.

Rules are applied until nothing new is learned. If nothing is certain, the solver
guesses the hidden cell with the lowest estimated risk.

Flags are trusted as mines: a wrong flag placed by the player can mislead it.
"""
from __future__ import annotations

from ..game import Gameplay
from ..models import Coord, Move, Status

Constraint = tuple[frozenset[Coord], int]


class MinesweeperSolver:
    def next_move(self, game: Gameplay) -> Move | None:
        if game.is_over():
            return None
        if game.status is Status.READY:
            # The first click is always safe (the game keeps it clear of mines).
            return Move(Coord(game.width // 2, game.height // 2), flag=False, certain=True)

        constraints = self._constraints(game)
        safe, mines = self._deduce(constraints)
        if safe:
            return Move(min(safe), flag=False, certain=True)
        if mines:
            return Move(min(mines), flag=True, certain=True, risk=1.0)
        return self._best_guess(game, constraints)

    # -- constraints -----------------------------------------------------------

    def _hidden(self, game: Gameplay) -> set[Coord]:
        return {c for c, cell in game.cells.items() if not cell.revealed and not cell.flagged}

    def _constraints(self, game: Gameplay) -> list[Constraint]:
        hidden = self._hidden(game)
        out: list[Constraint] = []
        for c, cell in game.cells.items():
            if not cell.revealed or cell.adjacent == 0:
                continue
            around = game.neighbors(c)
            unknown = frozenset(n for n in around if n in hidden)
            if unknown:
                flagged = sum(game.cells[n].flagged for n in around)
                out.append((unknown, cell.adjacent - flagged))
        out.append((frozenset(hidden), game.mines - game.flags))
        return out

    def _deduce(self, constraints: list[Constraint]) -> tuple[set[Coord], set[Coord]]:
        safe: set[Coord] = set()
        mines: set[Coord] = set()
        changed = True
        while changed:
            changed = False
            # Remove what we already know, then drop duplicates and empty constraints.
            simplified = {
                (cells - safe - mines, n - len(cells & mines)) for cells, n in constraints
            }
            constraints = [(cells, n) for cells, n in simplified if cells]

            for cells, n in constraints:
                if n == 0:
                    safe |= cells
                    changed = True
                elif n == len(cells):
                    mines |= cells
                    changed = True
            if changed:
                continue

            for a, na in constraints:
                for b, nb in constraints:
                    if a < b:
                        diff, dn = b - a, nb - na
                        if dn == 0:
                            safe |= diff
                            changed = True
                        elif dn == len(diff):
                            mines |= diff
                            changed = True
        return safe, mines

    # -- guessing --------------------------------------------------------------

    def _best_guess(self, game: Gameplay, constraints: list[Constraint]) -> Move | None:
        hidden = self._hidden(game)
        if not hidden:
            return None
        density = (game.mines - game.flags) / len(hidden)
        # Rough estimate: a cell is as risky as the worst number touching it.
        # Cells touching no number take the overall density.
        risk = {c: density for c in hidden}
        touched: set[Coord] = set()
        for cells, n in constraints:
            if len(cells) == len(hidden):  # the global constraint, already in density
                continue
            for c in cells:
                r = n / len(cells)
                risk[c] = max(risk[c], r) if c in touched else r
                touched.add(c)
        best = min(hidden, key=lambda c: (risk[c], c))
        return Move(best, flag=False, certain=False, risk=risk[best])
