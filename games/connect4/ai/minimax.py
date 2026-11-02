"""Minimax with alpha-beta pruning (negamax form): the classic, non-learning baseline.

It looks `depth` moves ahead, assuming both sides play their best, and scores the
positions it reaches with a hand-written heuristic (open lines of 2 and 3, center
control). Future learning agents (MCTS, self-play network) can be measured against it.
"""
from __future__ import annotations

import math
import random

from ..game import COLS, WINDOWS, Gameplay
from ..models import Piece
from .agent import Connect4Agent

_WIN = 1_000_000
_LINE_VALUE = (0, 0, 2, 5, 0)  # by pieces of one color in an open window of 4
# Try central columns first: they're usually best, which makes alpha-beta prune more.
_ORDER = sorted(range(COLS), key=lambda c: abs(c - COLS // 2))


class MinimaxAgent(Connect4Agent):
    def __init__(self, depth: int, rng: random.Random | None = None) -> None:
        self.depth = depth
        self.rng = rng or random.Random()

    def choose(self, game: Gameplay) -> int:
        g = game.copy()
        scores = {}
        alpha = -math.inf
        for col in self._moves(g):
            g.play(col)
            # Window widened by 1 (scores are integers): moves that tie the best are
            # scored exactly, not cut off with a mere bound, so the tie-break is fair.
            scores[col] = -self._negamax(g, self.depth - 1, -math.inf, -(alpha - 1))
            g.undo()
            alpha = max(alpha, scores[col])
        best = max(scores.values())
        # Random tie-break, so equal moves don't make the AI predictable.
        return self.rng.choice([c for c, s in scores.items() if s == best])

    def _negamax(self, g: Gameplay, depth: int, alpha: float, beta: float) -> float:
        """Score of the position for the side to move."""
        if g.winner is not Piece.NONE:
            return -(_WIN + depth)  # the previous move won; sooner losses are worse
        if g.is_draw:
            return 0
        if depth <= 0:
            return self._evaluate(g, g.turn)
        value = -math.inf
        for col in self._moves(g):
            g.play(col)
            value = max(value, -self._negamax(g, depth - 1, -beta, -alpha))
            g.undo()
            alpha = max(alpha, value)
            if alpha >= beta:
                break
        return value

    @staticmethod
    def _moves(g: Gameplay) -> list[int]:
        return [c for c in _ORDER if g.heights[c] < len(g.board[c])]

    @staticmethod
    def _evaluate(g: Gameplay, me: Piece) -> float:
        opp = me.other()
        center = g.board[COLS // 2]
        score = 3 * (center.count(me) - center.count(opp))
        for window in WINDOWS:
            cells = [g.board[c][r] for c, r in window]
            mine, theirs = cells.count(me), cells.count(opp)
            # Open lines only: a window holding both colors can never be completed.
            if theirs == 0:
                score += _LINE_VALUE[mine]
            elif mine == 0:
                score -= _LINE_VALUE[theirs]
        return score
