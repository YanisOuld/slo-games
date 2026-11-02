"""Connect Four views. They draw only; they never mutate the model (input lives in the Scene).

The board is an overlay with holes punched out: discs are drawn first, the board on
top, so falling discs really look like they slide down behind the front panel.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

import pygame

from engine.widget import Widget

from . import constants as k
from .game import COLS, ROWS, Gameplay
from .models import Piece

Color = tuple[int, int, int]
_SUPERSAMPLE = 3
_COLORS = {Piece.RED: k.COLOR_RED, Piece.YELLOW: k.COLOR_YELLOW}


def _darker(color: Color, factor: float) -> Color:
    return tuple(int(c * factor) for c in color)


@dataclass
class Falling:
    """A disc mid-drop: drawn at screen y instead of its slot."""

    col: int
    row: int
    y: float
    vy: float = 0.0
    bounced: bool = False


class BoardPanel(Widget):
    def __init__(self, rect: pygame.Rect) -> None:
        super().__init__(rect.x, rect.y, rect.w, rect.h)
        pad = k.BOARD_PAD
        # One extra row on top for the preview disc.
        self.cell = min((rect.w - 2 * k.MARGIN - 2 * pad) // COLS,
                        (rect.h - 2 * k.MARGIN - 2 * pad) // (ROWS + 1))
        board_w, board_h = self.cell * COLS + 2 * pad, self.cell * ROWS + 2 * pad
        top = rect.y + (rect.h - board_h - self.cell) // 2 + self.cell
        self.board_rect = pygame.Rect(rect.x + (rect.w - board_w) // 2, top, board_w, board_h)
        self.ox, self.oy = self.board_rect.x + pad, self.board_rect.y + pad
        self.radius = int(self.cell * k.DISC_RATIO)
        self.preview_y = self.board_rect.y - self.cell // 2 - 4

        self.overlay = self._make_overlay()
        self.discs = {p: self._make_disc(c) for p, c in _COLORS.items()}
        self.ghosts = {p: self._make_disc(c) for p, c in _COLORS.items()}
        for ghost in self.ghosts.values():
            ghost.set_alpha(140)

    # -- geometry used by the Scene ---------------------------------------------------------

    def column_at(self, pos: tuple[int, int]) -> int | None:
        x, y = pos
        if self.ox <= x < self.ox + COLS * self.cell and self.preview_y - self.cell // 2 <= y < self.board_rect.bottom:
            return (x - self.ox) // self.cell
        return None

    def slot_center(self, col: int, row: int) -> tuple[int, int]:
        return (self.ox + col * self.cell + self.cell // 2,
                self.oy + (ROWS - 1 - row) * self.cell + self.cell // 2)

    # -- drawing -----------------------------------------------------------------------------

    def draw(self, screen: pygame.Surface, game: Gameplay, falling: Falling | None,
             preview: tuple[int, Piece] | None, show_win: bool, t: float) -> None:
        shadow = self.board_rect.move(0, 8)
        pygame.draw.rect(screen, k.COLOR_SHADOW, shadow, border_radius=22)
        pygame.draw.rect(screen, k.COLOR_BEHIND, self.board_rect, border_radius=22)
        if preview is not None:
            col_rect = pygame.Rect(self.ox + preview[0] * self.cell, self.oy, self.cell, ROWS * self.cell)
            pygame.draw.rect(screen, k.COLOR_COLUMN, col_rect, border_radius=self.cell // 2)

        for col in range(COLS):
            for row in range(game.heights[col]):
                if falling is not None and (col, row) == (falling.col, falling.row):
                    continue
                self._blit_disc(screen, self.discs[game.board[col][row]], self.slot_center(col, row))
        if falling is not None:
            x, _ = self.slot_center(falling.col, falling.row)
            self._blit_disc(screen, self.discs[game.board[falling.col][falling.row]], (x, int(falling.y)))

        screen.blit(self.overlay, self.board_rect.topleft)

        if preview is not None:
            col, piece = preview
            x, _ = self.slot_center(col, 0)
            self._blit_disc(screen, self.ghosts[piece], (x, self.preview_y))
        if show_win and game.winning_cells:
            self._draw_win(screen, game, t)

    def _blit_disc(self, screen: pygame.Surface, disc: pygame.Surface, center: tuple[int, int]) -> None:
        screen.blit(disc, disc.get_rect(center=center))

    def _draw_win(self, screen: pygame.Surface, game: Gameplay, t: float) -> None:
        centers = [self.slot_center(c, r) for c, r in game.winning_cells]
        pulse = 0.5 + 0.5 * math.sin(t * 6)
        pygame.draw.line(screen, k.COLOR_WIN, centers[0], centers[-1], 4)
        for center in centers:
            pygame.draw.circle(screen, k.COLOR_WIN, center, self.radius + 2 + int(3 * pulse), 3)

    # -- sprites: drawn bigger then smoothly scaled down, for anti-aliased edges ----------

    def _make_overlay(self) -> pygame.Surface:
        ss = _SUPERSAMPLE
        w, h = self.board_rect.size
        big = pygame.Surface((w * ss, h * ss), pygame.SRCALPHA)
        pygame.draw.rect(big, k.COLOR_BOARD, big.get_rect(), border_radius=22 * ss)
        for col in range(COLS):
            for row in range(ROWS):
                cx = (k.BOARD_PAD + col * self.cell + self.cell // 2) * ss
                cy = (k.BOARD_PAD + row * self.cell + self.cell // 2) * ss
                pygame.draw.circle(big, k.COLOR_HOLE_RIM, (cx, cy), (self.radius + 4) * ss)
                # Drawing a transparent color replaces pixels: this punches the hole.
                pygame.draw.circle(big, (0, 0, 0, 0), (cx, cy), (self.radius + 1) * ss)
        return pygame.transform.smoothscale(big, (w, h))

    def _make_disc(self, color: Color) -> pygame.Surface:
        ss = _SUPERSAMPLE
        r = self.radius * ss
        big = pygame.Surface((2 * r, 2 * r), pygame.SRCALPHA)
        center = (r, r)
        pygame.draw.circle(big, _darker(color, 0.72), center, r)
        pygame.draw.circle(big, color, center, int(r * 0.86))
        pygame.draw.circle(big, _darker(color, 0.86), center, int(r * 0.62), max(ss, int(r * 0.06)))
        shine = tuple(int(c + (255 - c) * 0.45) for c in color)  # opaque: draw replaces pixels
        pygame.draw.circle(big, shine, (int(r * 0.7), int(r * 0.62)), int(r * 0.14))
        size = 2 * self.radius
        return pygame.transform.smoothscale(big, (size, size))
