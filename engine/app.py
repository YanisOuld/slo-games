"""The single main loop. One App, one loop; changing screen = changing scene."""
from __future__ import annotations

import logging
from typing import Callable

import pygame

from . import constants as c
from .scene import Scene

log = logging.getLogger(__name__)


class App:
    def __init__(self, title: str, first_scene: Callable[[], Scene]) -> None:
        # first_scene is a factory: scenes build fonts, so they must be created
        # AFTER pygame.init(), not passed in already-built.
        pygame.init()
        self.screen = pygame.display.set_mode((c.SCREEN_WIDTH, c.SCREEN_HEIGHT))
        pygame.display.set_caption(title)
        self.clock = pygame.time.Clock()
        self.running = False
        self._scene = first_scene()
        self._scene.on_enter(self)

    def change_scene(self, scene: Scene) -> None:
        log.info("scene %s -> %s", type(self._scene).__name__, type(scene).__name__)
        self._scene = scene
        self._scene.on_enter(self)

    def quit(self) -> None:
        self.running = False

    def run(self) -> None:
        log.info("app start")
        self.running = True
        while self.running:
            dt = self.clock.tick(c.FPS) / 1000.0  # seconds since last frame
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                else:
                    self._scene.handle_event(event)
            self._scene.update(dt)
            self.screen.fill(c.BG)
            self._scene.draw(self.screen)
            pygame.display.flip()
        pygame.quit()
        log.info("app stop")
