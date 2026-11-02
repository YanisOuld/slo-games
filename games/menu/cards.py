"""Game cards for the main menu: a drawn icon, a name, a tagline, a hover lift.

Icons come from games/icons.py. A game without an entry in _STYLES gets a
generic look, so adding a game to the registry is enough.
"""
from __future__ import annotations

from typing import Callable

import pygame

from engine import theme
from engine.widget import Widget
from games.icons import draw_icon

Color = tuple[int, int, int]

CARD_BG = theme.SURFACE_RAISED
CARD_BG_HOVER = theme.SURFACE_HOVER
CARD_SHADOW = (6, 6, 10)
ICON_BG = theme.SURFACE
TEXT = theme.TEXT
TEXT_DIM = theme.TEXT_DIM

_LIFT = 8          # px a hovered card rises
_EASE = 12.0       # hover animation speed (higher = snappier)


# name -> (accent color, tagline)
_STYLES: dict[str, tuple[Color, str]] = {
    "Binairo": (theme.BLUE, "Puzzle logique"),
    "Snake": (theme.GREEN, "Arcade + IA"),
    "Démineur": (theme.RED, "Logique + indices"),
    "Runner": (theme.YELLOW, "Course infinie"),
}


class GameCard(Widget):
    def __init__(self, rect: pygame.Rect, name: str, on_click: Callable[[], None],
                 font_name: pygame.font.Font, font_tag: pygame.font.Font) -> None:
        super().__init__(rect.x, rect.y, rect.w, rect.h)
        self.name = name
        self.on_click = on_click
        self.accent, self.tagline = _STYLES.get(
            name, (theme.PURPLE, "Jouer"))
        self.font_name = font_name
        self.font_tag = font_tag
        self.lift = 0.0  # current hover lift, eased toward 0 or _LIFT

        # The icon never changes: draw it once.
        icon_rect = pygame.Rect(0, 0, rect.w - 24, int(rect.h * 0.58))
        self.icon_surface = pygame.Surface(icon_rect.size, pygame.SRCALPHA)
        pygame.draw.rect(self.icon_surface, ICON_BG, icon_rect, border_radius=12)
        draw_icon(name, self.icon_surface, icon_rect, self.accent)

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
