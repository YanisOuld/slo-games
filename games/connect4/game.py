"""Connect Four rules. No pygame.

Convention: board[col][row], row 0 is the BOTTOM (pieces fall toward row 0).
play() and undo() are cheap and exact inverses, so search algorithms (minimax,
MCTS) can explore on one board without copying it at every node.
"""
from __future__ import annotations

import logging

from .models import Piece

log = logging.getLogger(__name__)

COLS, ROWS = 7, 6
CONNECT = 4

Cell = tuple[int, int]  # (col, row)

# Every line of 4 cells on the board: used to find wins and by evaluation heuristics.
WINDOWS: list[tuple[Cell, ...]] = [
    tuple((c + i * dc, r + i * dr) for i in range(CONNECT))
    for c in range(COLS)
    for r in range(ROWS)
    for dc, dr in ((1, 0), (0, 1), (1, 1), (1, -1))
    if 0 <= c + (CONNECT - 1) * dc < COLS and 0 <= r + (CONNECT - 1) * dr < ROWS
]


class Gameplay:
    def __init__(self, starter: Piece = Piece.RED) -> None:
        self.reset(starter)

    def reset(self, starter: Piece = Piece.RED) -> None:
        self.board = [[Piece.NONE] * ROWS for _ in range(COLS)]
        self.heights = [0] * COLS          # pieces in each column
        self.turn = starter                # whose move it is
        self.history: list[int] = []       # columns played, in order
        self.winner = Piece.NONE
        self.winning_cells: list[Cell] = []

    # -- public API ----------------------------------------------------------------

    @property
    def is_draw(self) -> bool:
        return self.winner is Piece.NONE and len(self.history) == COLS * ROWS

    def is_over(self) -> bool:
        return self.winner is not Piece.NONE or self.is_draw

    def can_play(self, col: int) -> bool:
        return not self.is_over() and 0 <= col < COLS and self.heights[col] < ROWS

    def legal_moves(self) -> list[int]:
        return [c for c in range(COLS) if self.can_play(c)]

    def play(self, col: int) -> int:
        """Drop the current player's piece in col. Returns the row it lands on."""
        if not self.can_play(col):
            raise ValueError(f"illegal move: column {col}")
        row = self.heights[col]
        piece = self.turn
        self.board[col][row] = piece
        self.heights[col] += 1
        self.history.append(col)
        self.winning_cells = self._line_through(col, row, piece)
        if self.winning_cells:
            self.winner = piece
        self.turn = piece.other()
        return row

    def undo(self) -> None:
        col = self.history.pop()
        self.heights[col] -= 1
        row = self.heights[col]
        self.turn = self.board[col][row]
        self.board[col][row] = Piece.NONE
        self.winner = Piece.NONE
        self.winning_cells = []

    def copy(self) -> "Gameplay":
        g = Gameplay.__new__(Gameplay)
        g.board = [col[:] for col in self.board]
        g.heights = self.heights[:]
        g.turn = self.turn
        g.history = self.history[:]
        g.winner = self.winner
        g.winning_cells = self.winning_cells[:]
        return g

    # -- helpers -------------------------------------------------------------------

    def _line_through(self, col: int, row: int, piece: Piece) -> list[Cell]:
        """The 4+ aligned cells through (col, row) if the piece there completes a line."""
        for dc, dr in ((1, 0), (0, 1), (1, 1), (1, -1)):
            line = [(col, row)]
            for sign in (1, -1):
                c, r = col + sign * dc, row + sign * dr
                while 0 <= c < COLS and 0 <= r < ROWS and self.board[c][r] is piece:
                    line.append((c, r))
                    c, r = c + sign * dc, r + sign * dr
            if len(line) >= CONNECT:
                return sorted(line)
        return []
