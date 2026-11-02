"""Snake views. They draw only; they never mutate the model (input lives in the Scene)."""
from __future__ import annotations

import pygame

from engine.widget import Widget

from . import constants as k
from .models import Coord


class BoardPanel(Widget):
    def __init__(self, rect: pygame.Rect, cols: int, rows: int) -> None:
        super().__init__(rect.x, rect.y, rect.width, rect.height)
        self.cols = cols
        self.rows = rows

        usable_w = rect.width - 2 * k.PADDING
        usable_h = rect.height - 2 * k.PADDING
        self.box = min(usable_w // cols, usable_h // rows)
        self.board_w = self.box * cols
        self.board_h = self.box * rows
        # Center the board inside its panel.
        self.ox = rect.x + (rect.width - self.board_w) // 2
        self.oy = rect.y + (rect.height - self.board_h) // 2

    def draw(self, screen: pygame.Surface, snake: list[Coord], food: Coord) -> None:
        pygame.draw.rect(screen, k.COLOR_GRID_BG,
                         (self.ox, self.oy, self.board_w, self.board_h))
        self._draw_grid_lines(screen)
        self._draw_cell(screen, food, k.COLOR_FOOD)
        for i, segment in enumerate(snake):
            self._draw_cell(screen, segment, k.COLOR_SNAKE_HEAD if i == 0 else k.COLOR_SNAKE_BODY)

    def _draw_grid_lines(self, screen: pygame.Surface) -> None:
        for c in range(self.cols + 1):
            x = self.ox + c * self.box
            pygame.draw.line(screen, k.COLOR_GRID_LINE, (x, self.oy), (x, self.oy + self.board_h))
        for r in range(self.rows + 1):
            y = self.oy + r * self.box
            pygame.draw.line(screen, k.COLOR_GRID_LINE, (self.ox, y), (self.ox + self.board_w, y))

    def _draw_cell(self, screen: pygame.Surface, coord: Coord, color: tuple[int, int, int]) -> None:
        cell = pygame.Rect(
            self.ox + coord.x * self.box + k.CELL_GAP,
            self.oy + coord.y * self.box + k.CELL_GAP,
            self.box - 2 * k.CELL_GAP,
            self.box - 2 * k.CELL_GAP,
        )
        pygame.draw.rect(screen, color, cell, border_radius=k.CELL_RADIUS)
