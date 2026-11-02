"""Main menu: lists games from the registry as cards and launches the one picked.

Cards sit in a horizontal carousel showing _VISIBLE games at a time; arrows (and the
arrow keys / mouse wheel) slide it when there are more games than fit.
"""
from __future__ import annotations

import math
import random

import pygame

from engine import constants as sc
from engine import theme
from engine.scene import Scene
from games.registry import GAMES

from .cards import GameCard

BG_TOP = theme.BG
BG_BOTTOM = (28, 26, 46)
PARTICLE = (90, 84, 150)
TITLE = theme.TEXT
TITLE_SHADOW = (56, 40, 104)
SUBTITLE = theme.TEXT_DIM
TITLE_ACCENTS = (theme.BLUE, theme.GREEN, theme.RED, theme.YELLOW, theme.PURPLE)
ARROW_BG = theme.SURFACE_RAISED
ARROW_BG_HOVER = theme.SURFACE_HOVER
ARROW_FG = theme.TEXT
DOT = theme.SURFACE_HOVER
DOT_ACTIVE = theme.TEXT_DIM

_VISIBLE = 4
_CARD_W, _CARD_H, _GAP = 200, 260, 24
_CARDS_Y = 215
_STRIP_W = _VISIBLE * _CARD_W + (_VISIBLE - 1) * _GAP
_STRIP_X = (sc.SCREEN_WIDTH - _STRIP_W) // 2
_ARROW_R = 22
_SLIDE_EASE = 10.0  # carousel animation speed


class MenuScene(Scene):
    # Carousel position, kept across visits so "Retour au menu" lands where you left.
    _first_visible = 0

    def __init__(self) -> None:
        self.font_title = pygame.font.SysFont(None, 110)
        self.font_sub = pygame.font.SysFont(None, 30)
        self.font_name = pygame.font.SysFont(None, 38)
        self.font_tag = pygame.font.SysFont(None, 24)
        self.time = 0.0

        self.background = pygame.Surface((sc.SCREEN_WIDTH, sc.SCREEN_HEIGHT))
        for y in range(sc.SCREEN_HEIGHT):
            t = y / sc.SCREEN_HEIGHT
            color = [int(a + (b - a) * t) for a, b in zip(BG_TOP, BG_BOTTOM)]
            pygame.draw.line(self.background, color, (0, y), (sc.SCREEN_WIDTH, y))
        # Slow drifting dots: (x, y, speed px/s, radius).
        rng = random.Random(7)
        self.particles = [
            [rng.uniform(0, sc.SCREEN_WIDTH), rng.uniform(0, sc.SCREEN_HEIGHT),
             rng.uniform(8, 26), rng.choice((1, 1, 2, 2, 3))]
            for _ in range(60)
        ]
        self.cards = self._build_cards()
        self.max_first = max(0, len(self.cards) - _VISIBLE)
        self.first = min(MenuScene._first_visible, self.max_first)  # leftmost visible card
        self.offset = float(self._target_offset())                # current slide, in px
        self.clip = pygame.Rect(_STRIP_X - 14, _CARDS_Y - 14, _STRIP_W + 28, _CARD_H + 30)
        arrow_y = _CARDS_Y + _CARD_H // 2
        self.arrow_left = pygame.Rect(0, 0, 2 * _ARROW_R, 2 * _ARROW_R)
        self.arrow_left.center = (_STRIP_X // 2 - 4, arrow_y)
        self.arrow_right = self.arrow_left.copy()
        self.arrow_right.center = (sc.SCREEN_WIDTH - _STRIP_X // 2 + 4, arrow_y)

    def _build_cards(self) -> list[GameCard]:
        # One horizontal strip; _layout() slides it under the visible window.
        return [
            GameCard(pygame.Rect(0, _CARDS_Y, _CARD_W, _CARD_H), name, self._launcher(factory),
                     self.font_name, self.font_tag)
            for name, factory in GAMES.items()
        ]

    def _target_offset(self) -> int:
        return self.first * (_CARD_W + _GAP)

    def _layout(self) -> None:
        for i, card in enumerate(self.cards):
            card.rect.x = _STRIP_X + i * (_CARD_W + _GAP) - round(self.offset)

    def _scroll(self, step: int) -> None:
        self.first = max(0, min(self.max_first, self.first + step))
        MenuScene._first_visible = self.first

    def _can_scroll(self, step: int) -> bool:
        return 0 <= self.first + step <= self.max_first

    def _launcher(self, factory):
        # Dedicated function captures factory's value, not the loop variable.
        return lambda: self.app.change_scene(factory())

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for rect, step in ((self.arrow_left, -1), (self.arrow_right, 1)):
                if self._can_scroll(step) and rect.collidepoint(event.pos):
                    self._scroll(step)
                    return
        elif event.type == pygame.MOUSEWHEEL:
            self._scroll(-1 if event.y > 0 or event.x < 0 else 1)
            return
        elif event.type == pygame.KEYDOWN and event.key in (pygame.K_LEFT, pygame.K_RIGHT):
            self._scroll(-1 if event.key == pygame.K_LEFT else 1)
            return
        for card in self._visible_cards():
            card.handle_event(event)

    def _visible_cards(self) -> list[GameCard]:
        # Only fully visible cards react, so a half-hidden card can't be clicked.
        return [c for c in self.cards if self.clip.contains(c.rect)]

    def update(self, dt: float) -> None:
        self.time += dt
        for p in self.particles:
            p[1] -= p[2] * dt
            if p[1] < -5:
                p[1] = sc.SCREEN_HEIGHT + 5
        target = self._target_offset()
        self.offset += (target - self.offset) * min(1.0, dt * _SLIDE_EASE)
        if abs(target - self.offset) < 0.5:
            self.offset = float(target)
        self._layout()
        visible = self._visible_cards()
        for card in self.cards:
            if card in visible:
                card.update(dt)
            else:
                card.lift = 0.0

    def draw(self, screen: pygame.Surface) -> None:
        screen.blit(self.background, (0, 0))
        for x, y, _, radius in self.particles:
            pygame.draw.circle(screen, PARTICLE, (int(x), int(y)), radius)
        self._draw_title(screen)
        screen.set_clip(self.clip)  # cards slide in and out of the window
        for card in self.cards:
            if card.rect.colliderect(self.clip):
                card.draw(screen)
        screen.set_clip(None)
        if self.max_first > 0:
            self._draw_arrow(screen, self.arrow_left, -1)
            self._draw_arrow(screen, self.arrow_right, 1)
            self._draw_dots(screen)

    def _draw_arrow(self, screen: pygame.Surface, rect: pygame.Rect, step: int) -> None:
        if not self._can_scroll(step):
            return  # only shown when there's something that way
        hovered = rect.collidepoint(pygame.mouse.get_pos())
        pygame.draw.circle(screen, ARROW_BG_HOVER if hovered else ARROW_BG, rect.center, _ARROW_R)
        pygame.draw.circle(screen, theme.BORDER, rect.center, _ARROW_R, 1)
        cx, cy = rect.center
        tip = 6 * step
        pygame.draw.lines(screen, ARROW_FG, False,
                          [(cx - tip, cy - 9), (cx + tip, cy), (cx - tip, cy + 9)], 3)

    def _draw_dots(self, screen: pygame.Surface) -> None:
        # One dot per game; the visible ones are brighter.
        n = len(self.cards)
        x0 = sc.SCREEN_WIDTH // 2 - (n - 1) * 9
        y = _CARDS_Y + _CARD_H + 34
        for i in range(n):
            visible = self.first <= i < self.first + _VISIBLE
            pygame.draw.circle(screen, DOT_ACTIVE if visible else DOT, (x0 + i * 18, y), 4)

    def _draw_title(self, screen: pygame.Surface) -> None:
        cx = sc.SCREEN_WIDTH // 2
        y = 95 + 4 * math.sin(self.time * 1.6)  # gentle float
        shadow = self.font_title.render("SLO Games", True, TITLE_SHADOW)
        screen.blit(shadow, shadow.get_rect(center=(cx + 4, y + 5)))
        title = self.font_title.render("SLO Games", True, TITLE)
        screen.blit(title, title.get_rect(center=(cx, y)))
        # One dot per game color under the title.
        for i, color in enumerate(TITLE_ACCENTS):
            x = cx - (len(TITLE_ACCENTS) - 1) * 15 + i * 30
            pygame.draw.circle(screen, color, (x, int(y) + 50), 6)
        sub = self.font_sub.render("Choisis un jeu", True, SUBTITLE)
        screen.blit(sub, sub.get_rect(center=(cx, 182)))
