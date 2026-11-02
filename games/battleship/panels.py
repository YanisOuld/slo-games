"""Battleship views. They draw only; they never mutate the model (input lives in the Scene).

Cheap to draw (Raspberry Pi): water is pre-rendered once per grid, the heat map
once per turn; per frame it's just a few rects and circles.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

import pygame

from engine.widget import Widget

from . import constants as k
from .game import Board
from .models import SIZE, ShotResult, Ship

Color = tuple[int, int, int]


def _lerp(a: Color, b: Color, t: float) -> Color:
    return tuple(int(x + (y - x) * t) for x, y in zip(a, b))


_ship_cache: dict[tuple, pygame.Surface] = {}


def draw_ship(screen: pygame.Surface, rect: pygame.Rect, horizontal: bool, sunk: bool = False,
              color: Color | None = None, alpha: int | None = None) -> None:
    """A ship filling rect: capsule hull and turrets. Works at any size.
    Each look is built once and cached (cheap on a Raspberry Pi)."""
    key = (rect.size, horizontal, sunk, color, alpha)
    if key not in _ship_cache:
        _ship_cache[key] = _render_ship(rect.size, horizontal, sunk, color, alpha)
    screen.blit(_ship_cache[key], rect.topleft)


def _render_ship(size: tuple[int, int], horizontal: bool, sunk: bool,
                 color: Color | None, alpha: int | None) -> pygame.Surface:
    rect = pygame.Rect((0, 0), size)
    surf = pygame.Surface(size, pygame.SRCALPHA)
    r = surf.get_rect().inflate(-max(2, rect.h // 8 if horizontal else rect.w // 8),
                                -max(2, rect.h // 8 if horizontal else rect.w // 8))
    hull = color or (k.COLOR_SHIP_SUNK if sunk else k.COLOR_SHIP)
    radius = min(r.w, r.h) // 2
    pygame.draw.rect(surf, _lerp(hull, (0, 0, 0), 0.35), r, border_radius=radius)
    pygame.draw.rect(surf, hull, r.inflate(-2, -2), border_radius=radius)
    thick = min(r.w, r.h)
    length = max(r.w, r.h)
    turrets = max(1, length // max(1, thick) - 1)
    for i in range(turrets):   # little turrets along the deck
        t = (i + 1) / (turrets + 1)
        c = (r.x + r.w * t, r.centery) if horizontal else (r.centerx, r.y + r.h * t)
        pygame.draw.circle(surf, _lerp(hull, (0, 0, 0), 0.25), c, max(2, thick // 4))
    if sunk:
        pygame.draw.rect(surf, k.COLOR_SUNK_EDGE, r, width=2, border_radius=radius)
    if alpha is not None:
        surf.set_alpha(alpha)
    return surf


@dataclass
class Effect:
    x: int
    y: int
    result: ShotResult
    age: float = 0.0


class GridView(Widget):
    def __init__(self, x: int, y: int, cell: int, labels: bool) -> None:
        super().__init__(x, y, cell * SIZE, cell * SIZE)
        self.cell = cell
        self.labels = labels
        self.water = self._render_water()
        self.font_label = pygame.font.SysFont(None, 22)

    # -- geometry --------------------------------------------------------------------

    def cell_at(self, pos: tuple[int, int]) -> tuple[int, int] | None:
        x, y = pos[0] - self.rect.x, pos[1] - self.rect.y
        if 0 <= x < self.rect.w and 0 <= y < self.rect.h:
            return x // self.cell, y // self.cell
        return None

    def cell_rect(self, x: int, y: int, size: int = 1, horizontal: bool = True) -> pygame.Rect:
        w, h = (size, 1) if horizontal else (1, size)
        return pygame.Rect(self.rect.x + x * self.cell, self.rect.y + y * self.cell, w * self.cell, h * self.cell)

    def ship_rect(self, ship: Ship) -> pygame.Rect:
        return self.cell_rect(ship.x, ship.y, ship.size, ship.horizontal)

    # -- drawing ---------------------------------------------------------------------

    def draw(self, screen: pygame.Surface, board: Board, show_ships: bool, t: float,
             heat: pygame.Surface | None = None, effects: list[Effect] = (),
             hover: tuple[int, int] | None = None, hidden: int | None = None,
             reveal: bool = False) -> None:
        """show_ships: own fleet. reveal: game over, show the enemy's survivors faded.
        hidden: index of a ship being dragged (not drawn in place)."""
        screen.blit(self.water, self.rect.topleft)
        if heat is not None:
            screen.blit(heat, self.rect.topleft)
        for i, ship in enumerate(board.ships):
            if not ship.placed or i == hidden:
                continue
            if show_ships or ship.sunk:
                draw_ship(screen, self.ship_rect(ship), ship.horizontal, ship.sunk)
            elif reveal:
                draw_ship(screen, self.ship_rect(ship), ship.horizontal, alpha=110)
        self._draw_grid(screen)
        for (x, y), shot in board.shots.items():
            self._draw_marker(screen, x, y, shot.result, t)
        for effect in effects:
            self._draw_effect(screen, effect)
        if hover is not None:
            pygame.draw.rect(screen, k.COLOR_HOVER, self.cell_rect(*hover).inflate(-2, -2), 3, border_radius=6)
        if self.labels:
            self._draw_labels(screen)

    def draw_ghost(self, screen: pygame.Surface, x: int, y: int, size: int, horizontal: bool, valid: bool) -> None:
        rect = self.cell_rect(x, y, size, horizontal)
        draw_ship(screen, rect, horizontal, color=k.COLOR_VALID if valid else k.COLOR_INVALID, alpha=170)

    def make_heat(self, heat: list[list[float]]) -> pygame.Surface:
        """Translucent cold-to-hot overlay; built once per turn, not per frame."""
        surf = pygame.Surface(self.rect.size, pygame.SRCALPHA)
        for x in range(SIZE):
            for y in range(SIZE):
                v = heat[x][y]
                if v > 0.02:
                    color = _lerp(k.COLOR_HEAT_COLD, k.COLOR_HEAT_HOT, v)
                    rect = pygame.Rect(x * self.cell, y * self.cell, self.cell, self.cell).inflate(-2, -2)
                    pygame.draw.rect(surf, (*color, int(60 + 150 * v)), rect, border_radius=4)
        return surf

    def _draw_grid(self, screen: pygame.Surface) -> None:
        x0, y0 = self.rect.topleft
        for i in range(SIZE + 1):
            pygame.draw.line(screen, k.COLOR_GRID, (x0 + i * self.cell, y0), (x0 + i * self.cell, self.rect.bottom))
            pygame.draw.line(screen, k.COLOR_GRID, (x0, y0 + i * self.cell), (self.rect.right, y0 + i * self.cell))
        pygame.draw.rect(screen, k.COLOR_GRID, self.rect, 2, border_radius=4)

    def _draw_labels(self, screen: pygame.Surface) -> None:
        for i in range(SIZE):
            letter = self.font_label.render("ABCDEFGHIJ"[i], True, k.COLOR_LABEL)
            screen.blit(letter, letter.get_rect(center=(self.rect.x + i * self.cell + self.cell // 2, self.rect.y - 14)))
            number = self.font_label.render(str(i + 1), True, k.COLOR_LABEL)
            screen.blit(number, number.get_rect(center=(self.rect.x - 18, self.rect.y + i * self.cell + self.cell // 2)))

    def _draw_marker(self, screen: pygame.Surface, x: int, y: int, result: ShotResult, t: float) -> None:
        center = self.cell_rect(x, y).center
        r = self.cell // 2
        if result is ShotResult.MISS:
            pygame.draw.circle(screen, k.COLOR_MISS, center, max(2, r // 4))
            pygame.draw.circle(screen, k.COLOR_MISS, center, max(4, r // 2), 1)
        else:
            flicker = 1 + 0.12 * math.sin(t * 9 + x * 1.7 + y)   # burning, still cheap
            pygame.draw.circle(screen, k.COLOR_HIT, center, int(r * 0.55 * flicker))
            pygame.draw.circle(screen, k.COLOR_FIRE, center, int(r * 0.28 * flicker))

    def _draw_effect(self, screen: pygame.Surface, e: Effect) -> None:
        p = e.age / k.EFFECT_TIME   # 0 -> 1
        center = self.cell_rect(e.x, e.y).center
        if e.result is ShotResult.MISS:   # splash rings
            for ring in (0.0, 0.25):
                q = max(0.0, p - ring)
                if q > 0:
                    pygame.draw.circle(screen, k.COLOR_MISS, center, int(self.cell * (0.2 + 0.7 * q)), 2)
        else:                             # burst
            radius = int(self.cell * (0.3 + 0.9 * p))
            pygame.draw.circle(screen, k.COLOR_FIRE, center, radius, max(1, int(4 * (1 - p))))
            for i in range(8):
                a = i * math.pi / 4
                inner, outer = radius * 0.5, radius * 1.1
                pygame.draw.line(screen, k.COLOR_HIT,
                                 (center[0] + math.cos(a) * inner, center[1] + math.sin(a) * inner),
                                 (center[0] + math.cos(a) * outer, center[1] + math.sin(a) * outer), 2)

    def _render_water(self) -> pygame.Surface:
        w, h = self.rect.size
        surf = pygame.Surface((w, h))
        for y in range(h):
            pygame.draw.line(surf, _lerp(k.COLOR_WATER_TOP, k.COLOR_WATER_BOTTOM, y / h), (0, y), (w, y))
        step = max(6, self.cell // 3)
        for row in range(0, h, step * 2):   # little wave strokes
            for col in range(-step, w, step * 4):
                ox = col + (row // (step * 2)) % 2 * step * 2
                pygame.draw.arc(surf, k.COLOR_WAVE, (ox, row, step * 2, step), 0, math.pi, 1)
        return surf


def draw_fleet_status(screen: pygame.Surface, board: Board, x: int, y: int, cell: int,
                      vertical: bool, font: pygame.font.Font) -> None:
    """Silhouettes of a fleet: afloat ships bright, sunk ones dark and crossed out."""
    for i, ship in enumerate(board.ships):
        if vertical:
            rect = pygame.Rect(x, y + i * (cell + 10), ship.size * cell, cell)
        else:
            rect = pygame.Rect(x, y, ship.size * cell, cell)
            x += ship.size * cell + 12
        draw_ship(screen, rect, True, ship.sunk)
        if ship.sunk:
            pygame.draw.line(screen, k.COLOR_SUNK_EDGE, rect.midleft, rect.midright, 2)
        if vertical:
            label = font.render(ship.name, True, k.COLOR_TEXT_DIM if ship.sunk else k.COLOR_TEXT_SOFT)
            screen.blit(label, label.get_rect(midleft=(x + 5 * cell + 10, rect.centery)))


def draw_card(screen: pygame.Surface, center: tuple[int, int], title: str, lines: list[str],
              font_title: pygame.font.Font, font_body: pygame.font.Font) -> None:
    card = pygame.Rect(0, 0, 340, 90 + 32 * len(lines))
    card.center = center
    shade = pygame.Surface(card.size, pygame.SRCALPHA)
    pygame.draw.rect(shade, k.COLOR_CARD, shade.get_rect(), border_radius=20)
    screen.blit(shade, card.topleft)
    pygame.draw.rect(screen, k.COLOR_CARD_BORDER, card, 1, border_radius=20)
    label = font_title.render(title, True, k.COLOR_TEXT)
    screen.blit(label, label.get_rect(midtop=(card.centerx, card.y + 20)))
    pygame.draw.rect(screen, k.ACCENT, (card.centerx - 30, card.y + 72, 60, 4), border_radius=2)
    for i, line in enumerate(lines):
        text = font_body.render(line, True, k.COLOR_TEXT_SOFT)
        screen.blit(text, text.get_rect(midtop=(card.centerx, card.y + 88 + i * 32)))
