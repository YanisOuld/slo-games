"""Main menu: lists games from the registry as cards and launches the one picked."""
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
TITLE_ACCENTS = (theme.BLUE, theme.GREEN, theme.RED, theme.YELLOW)

_PER_ROW = 4
_CARD_W, _CARD_H, _GAP = 200, 260, 24


class MenuScene(Scene):
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

    def _build_cards(self) -> list[GameCard]:
        # Cards centered in rows of up to _PER_ROW, below the title.
        items = list(GAMES.items())
        rows = [items[i:i + _PER_ROW] for i in range(0, len(items), _PER_ROW)]
        card_h = min(_CARD_H, (sc.SCREEN_HEIGHT - 230) // len(rows) - _GAP)
        cards = []
        for r, row in enumerate(rows):
            total = len(row) * _CARD_W + (len(row) - 1) * _GAP
            x0 = (sc.SCREEN_WIDTH - total) // 2
            for i, (name, factory) in enumerate(row):
                rect = pygame.Rect(x0 + i * (_CARD_W + _GAP), 215 + r * (card_h + _GAP), _CARD_W, card_h)
                cards.append(GameCard(rect, name, self._launcher(factory), self.font_name, self.font_tag))
        return cards

    def _launcher(self, factory):
        # Dedicated function captures factory's value, not the loop variable.
        return lambda: self.app.change_scene(factory())

    def handle_event(self, event: pygame.event.Event) -> None:
        for card in self.cards:
            card.handle_event(event)

    def update(self, dt: float) -> None:
        self.time += dt
        for p in self.particles:
            p[1] -= p[2] * dt
            if p[1] < -5:
                p[1] = sc.SCREEN_HEIGHT + 5
        for card in self.cards:
            card.update(dt)

    def draw(self, screen: pygame.Surface) -> None:
        screen.blit(self.background, (0, 0))
        for x, y, _, radius in self.particles:
            pygame.draw.circle(screen, PARTICLE, (int(x), int(y)), radius)
        self._draw_title(screen)
        for card in self.cards:
            card.draw(screen)

    def _draw_title(self, screen: pygame.Surface) -> None:
        cx = sc.SCREEN_WIDTH // 2
        y = 95 + 4 * math.sin(self.time * 1.6)  # gentle float
        shadow = self.font_title.render("SLO Games", True, TITLE_SHADOW)
        screen.blit(shadow, shadow.get_rect(center=(cx + 4, y + 5)))
        title = self.font_title.render("SLO Games", True, TITLE)
        screen.blit(title, title.get_rect(center=(cx, y)))
        # One dot per game color under the title.
        for i, color in enumerate(TITLE_ACCENTS):
            pygame.draw.circle(screen, color, (cx - 45 + i * 30, int(y) + 50), 6)
        sub = self.font_sub.render("Choisis un jeu", True, SUBTITLE)
        screen.blit(sub, sub.get_rect(center=(cx, 182)))
