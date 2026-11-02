"""Side panel shared by the games: header, stat tiles, action buttons, message, help.

Generic: it knows no game. Each game passes its title, accent color, icon, actions
and help sections, then gives it the live values (stats, message) every frame.

    ┌──────────────────────┐
    │ [icon]  Title        │  header
    │         subtitle     │
    │ ┌──────┐ ┌──────┐    │  stat tiles
    │ │LABEL │ │LABEL │    │
    │ │ 0:42 │ │ 34%  │    │
    │ └──────┘ └──────┘    │
    │ (↻) Nouvelle partie  │  actions (optional pill on the right: ON / Facile)
    │ ...                  │
    │ • message            │  toast
    │ SECTION ───────────  │  help: [key] description
    │ SLO games            │  footer
    └──────────────────────┘
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Callable

import pygame

from . import theme
from .widget import Widget

Color = tuple[int, int, int]

WIDTH = 320
_PAD = 28
_STATS_Y, _STATS_H = 108, 84
_BUTTONS_Y, _BUTTON_H, _BUTTON_GAP = 208, 40, 6
_TOAST_H = 34


def mix(a: Color, b: Color, t: float) -> Color:
    return tuple(int(x + (y - x) * t) for x, y in zip(a, b))


@dataclass
class Action:
    label: str
    on_click: Callable[[], None]
    icon: str = ""          # one of draw_icon's names
    primary: bool = False   # filled with the accent: the main action
    value: str = ""         # optional pill on the right, e.g. "OFF" or "Facile"
    value_on: bool = False  # pill filled with the accent


@dataclass
class Stat:
    label: str
    value: str
    progress: float | None = None  # 0..1: draws a thin bar under the value


# A help line: (key or symbol shown as a keycap, or None for a bullet; description).
HelpItem = tuple[str | None, str]


def draw_icon(screen: pygame.Surface, name: str, center: tuple[int, int], color: Color) -> None:
    """Small line icons (about 16 px) for the action buttons."""
    x, y = center
    if name == "new":       # circular arrow
        pygame.draw.arc(screen, color, (x - 7, y - 7, 14, 14), math.radians(60), math.radians(340), 2)
        pygame.draw.polygon(screen, color, [(x + 3, y - 10), (x + 8, y - 5), (x + 2, y - 3)])
    elif name == "check":
        pygame.draw.lines(screen, color, False, [(x - 7, y), (x - 2, y + 5), (x + 7, y - 5)], 3)
    elif name == "back":    # arrow pointing left
        pygame.draw.line(screen, color, (x - 7, y), (x + 7, y), 2)
        pygame.draw.lines(screen, color, False, [(x - 1, y - 6), (x - 7, y), (x - 1, y + 6)], 2)
    elif name == "ai":      # robot head
        pygame.draw.rect(screen, color, (x - 7, y - 4, 14, 11), width=2, border_radius=3)
        pygame.draw.line(screen, color, (x, y - 4), (x, y - 8), 2)
        pygame.draw.circle(screen, color, (x, y - 9), 2)
        for ex in (x - 3, x + 3):
            pygame.draw.circle(screen, color, (ex, y + 1), 1)
    elif name == "hint":    # light bulb
        pygame.draw.circle(screen, color, (x, y - 2), 6, 2)
        pygame.draw.rect(screen, color, (x - 3, y + 4, 7, 4), border_radius=1)
    elif name == "level":   # rising bars
        for i, h in enumerate((5, 9, 13)):
            pygame.draw.rect(screen, color, (x - 7 + i * 5, y + 6 - h, 4, h), border_radius=1)


class _ActionButton(Widget):
    def __init__(self, rect: pygame.Rect, action: Action, accent: Color,
                 font: pygame.font.Font, font_pill: pygame.font.Font) -> None:
        super().__init__(rect.x, rect.y, rect.w, rect.h)
        self.action = action
        self.accent = accent
        self.font = font
        self.font_pill = font_pill

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.rect.collidepoint(event.pos):
            self.action.on_click()

    def draw(self, screen: pygame.Surface) -> None:
        a = self.action
        hovered = self.rect.collidepoint(pygame.mouse.get_pos())
        if a.primary:
            bg = mix(theme.SURFACE_RAISED, self.accent, 0.45 if hovered else 0.32)
        else:
            bg = theme.SURFACE_HOVER if hovered else theme.SURFACE_RAISED
        pygame.draw.rect(screen, bg, self.rect, border_radius=10)
        if hovered and not a.primary:  # accent marker on the left edge
            pygame.draw.rect(screen, self.accent, (self.rect.x, self.rect.y + 10, 3, self.rect.h - 20),
                             border_radius=2)
        cy = self.rect.centery
        if a.icon:
            draw_icon(screen, a.icon, (self.rect.x + 24, cy), theme.TEXT if a.primary else self.accent)
        label = self.font.render(a.label, True, theme.TEXT)
        screen.blit(label, label.get_rect(midleft=(self.rect.x + 46, cy)))
        if a.value:
            text = self.font_pill.render(a.value, True, theme.BG if a.value_on else theme.TEXT_SOFT)
            pill = text.get_rect().inflate(16, 8)
            pill.midright = (self.rect.right - 12, cy)
            pygame.draw.rect(screen, self.accent if a.value_on else theme.SURFACE, pill, border_radius=pill.h // 2)
            screen.blit(text, text.get_rect(center=pill.center))


class Sidebar(Widget):
    def __init__(
        self,
        height: int,
        title: str,
        accent: Color,
        actions: list[Action],
        icon: pygame.Surface | None = None,
        sections: tuple[tuple[str, tuple[HelpItem, ...]], ...] = (),
    ) -> None:
        super().__init__(0, 0, WIDTH, height)
        self.title = title
        self.accent = accent
        self.icon = icon
        self.sections = sections
        self.font_title = pygame.font.SysFont(None, 46)
        self.font_sub = pygame.font.SysFont(None, 22)
        self.font_label = pygame.font.SysFont(None, 18)
        self.font_button = pygame.font.SysFont(None, 25)
        self.font_pill = pygame.font.SysFont(None, 19)
        self.font_toast = pygame.font.SysFont(None, 23)
        self.font_help = pygame.font.SysFont(None, 20)
        self.font_logo = pygame.font.SysFont(None, 34)
        self.inner_w = WIDTH - 2 * _PAD

        self.buttons = [
            _ActionButton(pygame.Rect(_PAD, _BUTTONS_Y + i * (_BUTTON_H + _BUTTON_GAP), self.inner_w, _BUTTON_H),
                          action, accent, self.font_button, self.font_pill)
            for i, action in enumerate(actions)
        ]
        self.toast_y = _BUTTONS_Y + len(actions) * (_BUTTON_H + _BUTTON_GAP) + 4
        self.background = self._make_background(height)

    def set_value(self, index: int, value: str, on: bool = False) -> None:
        self.buttons[index].action.value = value
        self.buttons[index].action.value_on = on

    def handle_event(self, event: pygame.event.Event) -> None:
        for b in self.buttons:
            b.handle_event(event)

    # -- drawing -----------------------------------------------------------------------

    def draw(self, screen: pygame.Surface, subtitle: str, stats: list[Stat],
             message: str = "", kind: str = "info") -> None:
        screen.blit(self.background, (0, 0))
        self._draw_header(screen, subtitle)
        self._draw_stats(screen, stats)
        for b in self.buttons:
            b.draw(screen)
        if message:
            self._draw_toast(screen, message, kind)
        y = self.toast_y + _TOAST_H + 14
        for title, items in self.sections:
            y = self._draw_section(screen, y, title, items) + 10
        self._draw_footer(screen)

    def _make_background(self, height: int) -> pygame.Surface:
        surf = pygame.Surface((WIDTH, height))
        surf.fill(theme.SURFACE)
        # Soft glow of the game's accent fading down from the top.
        glow = pygame.Surface((WIDTH, 240), pygame.SRCALPHA)
        for y in range(240):
            alpha = int(34 * (1 - y / 240) ** 2)
            pygame.draw.line(glow, (*self.accent, alpha), (0, y), (WIDTH, y))
        surf.blit(glow, (0, 0))
        pygame.draw.line(surf, theme.BORDER, (WIDTH - 1, 0), (WIDTH - 1, height))
        return surf

    def _draw_header(self, screen: pygame.Surface, subtitle: str) -> None:
        x = _PAD
        if self.icon is not None:
            badge = pygame.Rect(_PAD, 28, 54, 54)
            pygame.draw.rect(screen, mix(theme.SURFACE_RAISED, self.accent, 0.16), badge, border_radius=14)
            pygame.draw.rect(screen, mix(theme.BORDER, self.accent, 0.4), badge, width=1, border_radius=14)
            screen.blit(self.icon, self.icon.get_rect(center=badge.center))
            x = badge.right + 14
        screen.blit(self.font_title.render(self.title, True, theme.TEXT), (x, 30))
        screen.blit(self.font_sub.render(subtitle, True, theme.TEXT_DIM), (x, 66))

    def _draw_stats(self, screen: pygame.Surface, stats: list[Stat]) -> None:
        if not stats:
            return
        gap = 8
        w = (self.inner_w - gap * (len(stats) - 1)) // len(stats)
        font_value = pygame.font.SysFont(None, 40 if len(stats) < 3 else 32)
        for i, stat in enumerate(stats):
            tile = pygame.Rect(_PAD + i * (w + gap), _STATS_Y, w, _STATS_H)
            pygame.draw.rect(screen, theme.SURFACE_RAISED, tile, border_radius=12)
            screen.blit(self.font_label.render(stat.label.upper(), True, theme.TEXT_DIM), (tile.x + 12, tile.y + 12))
            screen.blit(font_value.render(stat.value, True, theme.TEXT), (tile.x + 12, tile.y + 32))
            if stat.progress is not None:
                bar = pygame.Rect(tile.x + 12, tile.bottom - 16, tile.w - 24, 5)
                pygame.draw.rect(screen, theme.SURFACE, bar, border_radius=3)
                filled = int(bar.w * max(0.0, min(1.0, stat.progress)))
                if filled:
                    pygame.draw.rect(screen, self.accent, (bar.x, bar.y, max(5, filled), bar.h), border_radius=3)

    def _draw_toast(self, screen: pygame.Surface, message: str, kind: str) -> None:
        color = {"success": theme.GREEN, "error": theme.RED}.get(kind)
        rect = pygame.Rect(_PAD, self.toast_y, self.inner_w, _TOAST_H)
        bg = mix(theme.SURFACE_RAISED, color, 0.16) if color else theme.SURFACE_RAISED
        fg = color or theme.TEXT_SOFT
        pygame.draw.rect(screen, bg, rect, border_radius=10)
        pygame.draw.circle(screen, color or self.accent, (rect.x + 16, rect.centery), 4)
        label = self.font_toast.render(message, True, fg)
        screen.blit(label, label.get_rect(midleft=(rect.x + 28, rect.centery)))

    def _draw_section(self, screen: pygame.Surface, y: int, title: str, items: tuple[HelpItem, ...]) -> int:
        label = self.font_label.render(title.upper(), True, theme.TEXT_DIM)
        screen.blit(label, (_PAD, y))
        line_y = y + label.get_height() // 2
        pygame.draw.line(screen, theme.BORDER, (_PAD + label.get_width() + 10, line_y), (WIDTH - _PAD, line_y))
        y += 24
        for key, text in items:
            x = _PAD
            if key is None:
                pygame.draw.circle(screen, self.accent, (x + 4, y + 8), 3)
                x += 16
            else:
                cap = self.font_help.render(key, True, theme.TEXT_SOFT)
                chip = pygame.Rect(x, y, max(20, cap.get_width() + 12), 19)
                pygame.draw.rect(screen, theme.SURFACE_RAISED, chip, border_radius=5)
                pygame.draw.rect(screen, theme.BORDER, chip, width=1, border_radius=5)
                screen.blit(cap, cap.get_rect(center=chip.center))
                x = chip.right + 8
            screen.blit(self.font_help.render(text, True, theme.TEXT_SOFT), (x, y + 2))
            y += 23
        return y

    def _draw_footer(self, screen: pygame.Surface) -> None:
        y = self.rect.bottom - 40
        logo = self.font_logo.render("SLO", True, self.accent)
        screen.blit(logo, (_PAD, y))
        screen.blit(self.font_help.render("games", True, theme.TEXT_DIM), (_PAD + logo.get_width() + 6, y + 9))
