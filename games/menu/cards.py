"""Game cards for the main menu: a drawn icon, a name, a tagline, a hover lift.

Icons are drawn with pygame primitives (no image files). A game without an
entry in _STYLES gets a generic look, so adding a game to the registry is enough.
"""
from __future__ import annotations

from typing import Callable

import pygame

from engine.widget import Widget

Color = tuple[int, int, int]

CARD_BG = (30, 32, 44)
CARD_BG_HOVER = (40, 43, 58)
CARD_SHADOW = (8, 8, 14)
ICON_BG = (20, 22, 32)
TEXT = (240, 240, 245)
TEXT_DIM = (150, 152, 170)

_LIFT = 8          # px a hovered card rises
_EASE = 12.0       # hover animation speed (higher = snappier)


# -- icons (each draws inside rect) ------------------------------------------------

def _icon_binairo(s: pygame.Surface, r: pygame.Rect, accent: Color) -> None:
    pattern = ("1010", "0101", "1100", "0011")
    cell = min(r.w, r.h) // 5
    ox, oy = r.centerx - 2 * cell, r.centery - 2 * cell
    for y, row in enumerate(pattern):
        for x, v in enumerate(row):
            center = (ox + x * cell + cell // 2, oy + y * cell + cell // 2)
            if v == "1":
                pygame.draw.circle(s, accent, center, cell // 2 - 4)
            else:
                pygame.draw.circle(s, (230, 230, 240), center, cell // 2 - 4, 3)


def _icon_snake(s: pygame.Surface, r: pygame.Rect, accent: Color) -> None:
    cell = min(r.w, r.h) // 6
    ox, oy = r.centerx - 3 * cell, r.centery - 3 * cell
    path = [(1, 4), (2, 4), (3, 4), (4, 4), (4, 3), (4, 2), (3, 2), (2, 2)]
    for i, (x, y) in enumerate(path):
        shade = tuple(max(0, c - i * 12) for c in accent)
        pygame.draw.rect(s, shade, (ox + x * cell + 2, oy + y * cell + 2, cell - 4, cell - 4),
                         border_radius=5)
    hx, hy = path[-1]
    pygame.draw.circle(s, (20, 20, 20), (ox + hx * cell + cell // 3, oy + hy * cell + cell // 3), 3)
    pygame.draw.circle(s, (220, 70, 80), (ox + 2 * cell - cell // 2 + cell, oy + cell + cell // 2), cell // 3)


def _icon_minesweeper(s: pygame.Surface, r: pygame.Rect, accent: Color) -> None:
    cell = min(r.w, r.h) // 4
    ox, oy = r.centerx - int(1.5 * cell), r.centery - int(1.5 * cell)
    font = pygame.font.SysFont(None, int(cell * 0.9), bold=True)
    grid = ("1F ", "12 ", "M1 ")
    numbers = {"1": (100, 160, 255), "2": (100, 210, 120)}
    for y, row in enumerate(grid):
        for x, v in enumerate(row):
            rect = pygame.Rect(ox + x * cell + 2, oy + y * cell + 2, cell - 4, cell - 4)
            hidden = v in " F"
            pygame.draw.rect(s, (70, 78, 98) if hidden else (44, 46, 58), rect, border_radius=4)
            if v in numbers:
                label = font.render(v, True, numbers[v])
                s.blit(label, label.get_rect(center=rect.center))
            elif v == "F":
                px = rect.x + rect.w * 2 // 5
                pygame.draw.line(s, (230, 230, 230), (px, rect.y + 8), (px, rect.bottom - 8), 2)
                pygame.draw.polygon(s, accent, [(px, rect.y + 8), (rect.right - 8, rect.y + 14),
                                                (px, rect.y + 20)])
            elif v == "M":
                pygame.draw.rect(s, accent, rect, border_radius=4)
                pygame.draw.circle(s, (15, 15, 15), rect.center, cell // 4)


def _icon_runner(s: pygame.Surface, r: pygame.Rect, accent: Color) -> None:
    ground = r.bottom - 28
    pygame.draw.rect(s, (60, 46, 52), (r.x, ground, r.w, r.bottom - ground),
                     border_bottom_left_radius=10, border_bottom_right_radius=10)
    pygame.draw.rect(s, (96, 200, 120), (r.x, ground, r.w, 6))
    body = pygame.Rect(r.x + 36, ground - 62, 30, 40)  # mid-jump
    pygame.draw.rect(s, (90, 190, 250), body, border_radius=7)
    pygame.draw.circle(s, (250, 250, 250), (body.right - 8, body.y + 11), 5)
    pygame.draw.circle(s, (20, 20, 30), (body.right - 6, body.y + 11), 2)
    pygame.draw.rect(s, (200, 120, 70), (r.x + 92, ground - 30, 28, 30), border_radius=3)
    for i in range(3):
        pygame.draw.circle(s, accent, (r.x + 82 + i * 20, ground - 62 + abs(i - 1) * 8), 6)
    drone = pygame.Rect(r.right - 56, ground - 70, 36, 16)
    pygame.draw.rect(s, (240, 170, 90), drone, border_radius=6)
    pygame.draw.circle(s, (240, 70, 80), drone.center, 3)


def _icon_generic(s: pygame.Surface, r: pygame.Rect, accent: Color) -> None:
    pygame.draw.polygon(s, accent, [(r.centerx - 22, r.centery - 28), (r.centerx - 22, r.centery + 28),
                                    (r.centerx + 30, r.centery)])


# name -> (accent color, tagline, icon)
_STYLES: dict[str, tuple[Color, str, Callable[[pygame.Surface, pygame.Rect, Color], None]]] = {
    "Binairo": ((100, 160, 255), "Puzzle logique", _icon_binairo),
    "Snake": ((120, 220, 120), "Arcade + IA", _icon_snake),
    "Démineur": ((240, 100, 100), "Logique + indices", _icon_minesweeper),
    "Runner": ((250, 210, 70), "Course infinie", _icon_runner),
}


class GameCard(Widget):
    def __init__(self, rect: pygame.Rect, name: str, on_click: Callable[[], None],
                 font_name: pygame.font.Font, font_tag: pygame.font.Font) -> None:
        super().__init__(rect.x, rect.y, rect.w, rect.h)
        self.name = name
        self.on_click = on_click
        self.accent, self.tagline, self.icon = _STYLES.get(
            name, ((200, 160, 255), "Jouer", _icon_generic))
        self.font_name = font_name
        self.font_tag = font_tag
        self.lift = 0.0  # current hover lift, eased toward 0 or _LIFT

        # The icon never changes: draw it once.
        icon_rect = pygame.Rect(0, 0, rect.w - 24, int(rect.h * 0.58))
        self.icon_surface = pygame.Surface(icon_rect.size, pygame.SRCALPHA)
        pygame.draw.rect(self.icon_surface, ICON_BG, icon_rect, border_radius=12)
        self.icon(self.icon_surface, icon_rect, self.accent)

    def hovered(self) -> bool:
        return self.rect.collidepoint(pygame.mouse.get_pos())

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.hovered():
            self.on_click()

    def update(self, dt: float) -> None:
        target = _LIFT if self.hovered() else 0.0
        self.lift += (target - self.lift) * min(1.0, dt * _EASE)

    def draw(self, screen: pygame.Surface) -> None:
        hover = self.lift / _LIFT  # 0..1
        card = self.rect.move(0, -round(self.lift))
        pygame.draw.rect(screen, CARD_SHADOW, self.rect.move(0, 6), border_radius=18)
        bg = [int(a + (b - a) * hover) for a, b in zip(CARD_BG, CARD_BG_HOVER)]
        pygame.draw.rect(screen, bg, card, border_radius=18)
        border = [int(a + (b - a) * hover) for a, b in zip(CARD_BG_HOVER, self.accent)]
        pygame.draw.rect(screen, border, card, width=2, border_radius=18)

        screen.blit(self.icon_surface, (card.x + 12, card.y + 12))
        name = self.font_name.render(self.name, True, TEXT)
        screen.blit(name, name.get_rect(midtop=(card.centerx, card.y + self.icon_surface.get_height() + 26)))
        tag = self.font_tag.render(self.tagline, True, TEXT_DIM)
        screen.blit(tag, tag.get_rect(midtop=(card.centerx, card.y + self.icon_surface.get_height() + 62)))
        # Accent bar along the bottom, wider on hover.
        bar_w = int(card.w * (0.25 + 0.5 * hover))
        pygame.draw.rect(screen, self.accent, (card.centerx - bar_w // 2, card.bottom - 14, bar_w, 4),
                         border_radius=2)
