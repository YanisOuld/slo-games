"""Main menu: lists games from the registry and launches the one picked."""
from __future__ import annotations

import pygame

from engine import constants as sc
from engine.scene import Scene
from engine.widget import Button
from games.registry import GAMES


class MenuScene(Scene):
    def __init__(self) -> None:
        self.font_title = pygame.font.SysFont(None, 96)
        self.font_body = pygame.font.SysFont(None, 40)

        bw, bh, gap = 320, 64, 20
        bx = (sc.SCREEN_WIDTH - bw) // 2
        self.buttons = [
            Button(bx, 240 + i * (bh + gap), bw, bh, name, self.font_body, self._launcher(factory))
            for i, (name, factory) in enumerate(GAMES.items())
        ]

    def _launcher(self, factory):
        # Dedicated function captures factory's value, not the loop variable.
        return lambda: self.app.change_scene(factory())

    def handle_event(self, event: pygame.event.Event) -> None:
        for b in self.buttons:
            b.handle_event(event)

    def draw(self, screen: pygame.Surface) -> None:
        title = self.font_title.render("SLO Games", True, (240, 240, 240))
        screen.blit(title, title.get_rect(center=(sc.SCREEN_WIDTH // 2, 130)))
        for b in self.buttons:
            b.draw(screen)
