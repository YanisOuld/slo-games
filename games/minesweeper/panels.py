"""Minesweeper views. They draw only; they never mutate the model (input lives in the Scene)."""
from __future__ import annotations

from typing import Callable

import pygame

from engine.widget import Button, Widget

from . import constants as k
from .game import Gameplay
from .models import Coord, Move, Statistics, Status


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
        self.font_number = pygame.font.SysFont(None, int(self.box * 0.95), bold=True)

    def cell_at(self, pos: tuple[int, int]) -> Coord | None:
        x, y = pos[0] - self.ox, pos[1] - self.oy
        if 0 <= x < self.board_w and 0 <= y < self.board_h:
            return Coord(x // self.box, y // self.box)
        return None

    def draw(self, screen: pygame.Surface, game: Gameplay, hint: Move | None) -> None:
        pygame.draw.rect(screen, k.COLOR_BOARD_BG,
                         (self.ox, self.oy, self.board_w, self.board_h))
        hovered = None if game.is_over() else self.cell_at(pygame.mouse.get_pos())
        lost = game.status is Status.LOST

        for coord, cell in game.cells.items():
            rect = self._cell_rect(coord)
            if cell.revealed:
                pygame.draw.rect(screen, k.COLOR_REVEALED, rect, border_radius=k.CELL_RADIUS)
                if cell.adjacent:
                    self._draw_number(screen, rect, cell.adjacent)
            elif coord == game.exploded:
                pygame.draw.rect(screen, k.COLOR_EXPLODED, rect, border_radius=k.CELL_RADIUS)
                self._draw_mine(screen, rect)
            elif lost and cell.mine and not cell.flagged:
                pygame.draw.rect(screen, k.COLOR_REVEALED, rect, border_radius=k.CELL_RADIUS)
                self._draw_mine(screen, rect)
            else:
                color = k.COLOR_HIDDEN_HOVER if coord == hovered else k.COLOR_HIDDEN
                pygame.draw.rect(screen, color, rect, border_radius=k.CELL_RADIUS)
                if cell.flagged:
                    self._draw_flag(screen, rect)
                    if lost and not cell.mine:
                        self._draw_cross(screen, rect)

        if hint is not None and not game.is_over():
            if not hint.certain:
                color = k.COLOR_HINT_GUESS
            else:
                color = k.COLOR_HINT_MINE if hint.flag else k.COLOR_HINT_SAFE
            pygame.draw.rect(screen, color, self._cell_rect(hint.coord).inflate(2, 2),
                             width=3, border_radius=k.CELL_RADIUS + 1)

    # -- drawing helpers -------------------------------------------------------

    def _cell_rect(self, coord: Coord) -> pygame.Rect:
        return pygame.Rect(
            self.ox + coord.x * self.box + k.CELL_GAP,
            self.oy + coord.y * self.box + k.CELL_GAP,
            self.box - 2 * k.CELL_GAP,
            self.box - 2 * k.CELL_GAP,
        )

    def _draw_number(self, screen: pygame.Surface, rect: pygame.Rect, n: int) -> None:
        label = self.font_number.render(str(n), True, k.NUMBER_COLORS[n])
        screen.blit(label, label.get_rect(center=rect.center))

    def _draw_mine(self, screen: pygame.Surface, rect: pygame.Rect) -> None:
        cx, cy = rect.center
        r = max(3, int(rect.width * 0.26))
        spike = int(r * 1.45)
        for dx, dy in ((1, 0), (0, 1), (1, 1), (1, -1)):
            s = spike if dx == 0 or dy == 0 else int(spike * 0.75)
            pygame.draw.line(screen, k.COLOR_MINE, (cx - dx * s, cy - dy * s),
                             (cx + dx * s, cy + dy * s), 2)
        pygame.draw.circle(screen, k.COLOR_MINE, (cx, cy), r)
        pygame.draw.circle(screen, (230, 230, 230), (cx - r // 3, cy - r // 3), max(1, r // 4))

    def _draw_flag(self, screen: pygame.Surface, rect: pygame.Rect) -> None:
        w, h = rect.width, rect.height
        pole_x = rect.x + int(w * 0.38)
        top, bottom = rect.y + int(h * 0.2), rect.y + int(h * 0.8)
        pygame.draw.line(screen, k.COLOR_FLAG_POLE, (pole_x, top), (pole_x, bottom), 2)
        pygame.draw.line(screen, k.COLOR_FLAG_POLE,
                         (rect.x + int(w * 0.25), bottom), (rect.x + int(w * 0.6), bottom), 2)
        pygame.draw.polygon(screen, k.COLOR_FLAG, [
            (pole_x, top),
            (rect.x + int(w * 0.75), top + int(h * 0.15)),
            (pole_x, top + int(h * 0.3)),
        ])

    def _draw_cross(self, screen: pygame.Surface, rect: pygame.Rect) -> None:
        inner = rect.inflate(-rect.width // 3, -rect.height // 3)
        pygame.draw.line(screen, k.COLOR_WRONG_FLAG, inner.topleft, inner.bottomright, 3)
        pygame.draw.line(screen, k.COLOR_WRONG_FLAG, inner.topright, inner.bottomleft, 3)


class NavigatorPanel(Widget):
    def __init__(
        self,
        rect: pygame.Rect,
        on_new_game: Callable[[], None],
        on_difficulty: Callable[[], None],
        on_hint: Callable[[], None],
        on_toggle_ai: Callable[[], None],
        on_back: Callable[[], None],
    ) -> None:
        super().__init__(rect.x, rect.y, rect.width, rect.height)
        self.font_title = pygame.font.SysFont(None, 64)
        self.font_body = pygame.font.SysFont(None, 32)
        self.font_help = pygame.font.SysFont(None, 24)
        self.font_logo = pygame.font.SysFont(None, 56)

        bx, bw, bh, gap, top = rect.x + 30, rect.width - 60, 46, 12, 110
        actions = (
            ("Nouvelle partie", on_new_game),
            ("Niveau : Facile", on_difficulty),
            ("Indice", on_hint),
            ("IA : OFF", on_toggle_ai),
            ("Retour au menu", on_back),
        )
        self.buttons = [
            Button(bx, top + i * (bh + gap), bw, bh, label, self.font_body, cb)
            for i, (label, cb) in enumerate(actions)
        ]
        # Kept to flip their labels.
        self.difficulty_button = self.buttons[1]
        self.ai_button = self.buttons[3]

    def set_difficulty_label(self, label: str) -> None:
        self.difficulty_button.text = f"Niveau : {label}"

    def set_ai_label(self, enabled: bool) -> None:
        self.ai_button.text = "IA : ON" if enabled else "IA : OFF"

    def handle_event(self, event: pygame.event.Event) -> None:
        for b in self.buttons:
            b.handle_event(event)

    def draw(self, screen: pygame.Surface, stats: Statistics, elapsed: float, message: str) -> None:
        pygame.draw.rect(screen, k.NAV_BG, self.rect)
        x = self.rect.x + 30
        screen.blit(self.font_title.render("Démineur", True, k.NAV_TITLE), (x, 36))
        for b in self.buttons:
            b.draw(screen)

        minutes, seconds = divmod(int(elapsed), 60)
        lines = (
            f"Mines restantes : {stats.mines_left}",
            f"Temps : {minutes:02d}:{seconds:02d}",
        )
        for i, line in enumerate(lines):
            screen.blit(self.font_body.render(line, True, k.NAV_TEXT), (x, 410 + i * 32))
        if message:
            screen.blit(self.font_body.render(message, True, k.NAV_TEXT), (x, 480))
        screen.blit(self.font_help.render("Clic gauche : révéler  |  Clic droit : drapeau",
                                          True, k.NAV_HELP), (x, 516))
        screen.blit(self.font_logo.render("SLO", True, k.NAV_LOGO), (x, self.rect.bottom - 52))
