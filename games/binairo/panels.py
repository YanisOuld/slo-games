"""Binairo views. They draw and report clicks via callbacks; they never mutate the model."""
from __future__ import annotations

from typing import Callable

import pygame

from engine.widget import Button, Widget

from . import constants as k
from .game import Grid
from .models import BoxType, Hint, Statistics

_CELL_COLORS = {
    BoxType.NONE: k.COLOR_EMPTY,
    BoxType.WHITE: k.COLOR_WHITE,
    BoxType.BLACK: k.COLOR_BLACK,
}


class BoardPanel(Widget):
    def __init__(self, rect: pygame.Rect, size: int, on_cell_click: Callable[[int, int], None]) -> None:
        super().__init__(rect.x, rect.y, rect.width, rect.height)
        self.size = size
        self.on_cell_click = on_cell_click

        usable = min(rect.width, rect.height) - 2 * k.PADDING - k.STAT_MARGIN
        self.box = usable // size
        self.board_px = self.box * size
        self.ox = rect.x + k.PADDING
        self.oy = rect.y + k.PADDING

        self.font_hint = pygame.font.SysFont(None, int(self.box * 0.6))
        self.font_stat = pygame.font.SysFont(None, int(self.box * 0.4))

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type != pygame.MOUSEBUTTONDOWN or event.button != 1:
            return
        mx, my = event.pos
        if self.ox <= mx < self.ox + self.board_px and self.oy <= my < self.oy + self.board_px:
            self.on_cell_click((mx - self.ox) // self.box, (my - self.oy) // self.box)

    def draw(self, screen: pygame.Surface, grid: Grid, hints: list[Hint], stats: Statistics) -> None:
        self._draw_cells(screen, grid)
        self._draw_hints(screen, hints)
        self._draw_stats(screen, stats)

    def _draw_cells(self, screen: pygame.Surface, grid: Grid) -> None:
        for c in range(self.size):
            for r in range(self.size):
                cell = pygame.Rect(
                    self.ox + c * self.box + k.CELL_GAP,
                    self.oy + r * self.box + k.CELL_GAP,
                    self.box - 2 * k.CELL_GAP,
                    self.box - 2 * k.CELL_GAP,
                )
                pygame.draw.rect(screen, _CELL_COLORS[grid[c][r].type], cell, border_radius=k.CELL_RADIUS)
                if grid[c][r].is_blocked:
                    ...
                    cell = pygame.Rect(
                        self.ox + c * self.box + self.box // 3,
                        self.oy + r * self.box + self.box // 3,
                        self.box // 3,
                        self.box // 3,
                    )
                    pygame.draw.rect(screen, "grey", cell, border_radius=100)

    def _draw_hints(self, screen: pygame.Surface, hints: list[Hint]) -> None:
        for h in hints:
            c1, c2 = h.coord1, h.coord2
            if h.direction.is_horizontal():
                px = self.ox + max(c1.x, c2.x) * self.box
                py = self.oy + (c1.y + 0.5) * self.box
            else:
                px = self.ox + (c1.x + 0.5) * self.box
                py = self.oy + max(c1.y, c2.y) * self.box
            glyph = self.font_hint.render(h.type.value, True, k.COLOR_HINT)
            screen.blit(glyph, glyph.get_rect(center=(int(px), int(py))))

    def _draw_stats(self, screen: pygame.Surface, stats: Statistics) -> None:
        half = self.size // 2
        for c in range(self.size):
            white, black, _ = stats.per_col[c]
            self._stat(screen, f"{half - white}/{half - black}",
                       self.ox + c * self.box + self.box / 2,
                       self.oy + self.board_px + k.STAT_MARGIN / 2)

        for r in range(self.size):
            white, black, _ = stats.per_row[r]
            self._stat(screen, f"{half - white}/{half - black}",
                       self.ox + self.board_px + k.STAT_MARGIN / 2,
                       self.oy + r * self.box + self.box / 2)

    def _stat(self, screen: pygame.Surface, text: str, cx: float, cy: float) -> None:
        surface = self.font_stat.render(text, True, k.COLOR_STAT)
        screen.blit(surface, surface.get_rect(center=(int(cx), int(cy))))


class NavigatorPanel(Widget):
    def __init__(
        self,
        rect: pygame.Rect,
        on_new_game: Callable[[], None],
        on_verify: Callable[[], None],
        on_back: Callable[[], None],
    ) -> None:
        super().__init__(rect.x, rect.y, rect.width, rect.height)
        self.font_title = pygame.font.SysFont(None, 72)
        self.font_body = pygame.font.SysFont(None, 32)
        self.font_logo = pygame.font.SysFont(None, 56)

        bx, bw, bh, gap, top = rect.x + 30, rect.width - 60, 56, 18, 170
        actions = (("Nouvelle partie", on_new_game), ("Vérifier", on_verify), ("Retour au menu", on_back))
        self.buttons = [
            Button(bx, top + i * (bh + gap), bw, bh, label, self.font_body, cb)
            for i, (label, cb) in enumerate(actions)
        ]

    def handle_event(self, event: pygame.event.Event) -> None:
        for b in self.buttons:
            b.handle_event(event)

    def draw(self, screen: pygame.Surface, elapsed: float, message: str) -> None:
        pygame.draw.rect(screen, k.NAV_BG, self.rect)
        screen.blit(self.font_title.render("Binairo+", True, k.NAV_TITLE), (self.rect.x + 30, 40))
        for b in self.buttons:
            b.draw(screen)
        minutes, seconds = divmod(int(elapsed), 60)
        screen.blit(self.font_body.render(f"Temps : {minutes:02d}:{seconds:02d}", True, k.NAV_TEXT), (self.rect.x + 30, 380))
        if message:
            screen.blit(self.font_body.render(message, True, k.NAV_TEXT), (self.rect.x + 30, 430))
        screen.blit(self.font_logo.render("SLO", True, k.NAV_LOGO), (self.rect.x + 30, self.rect.bottom - 70))
