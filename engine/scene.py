"""Scene: one screen of the app (menu, a game, a win screen...)."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

import pygame

if TYPE_CHECKING:
    from .app import App


class Scene(ABC):
    """Lifecycle driven by App: on_enter, then handle_event/update/draw each frame."""

    app: "App"

    def on_enter(self, app: "App") -> None:
        self.app = app

    def handle_event(self, event: pygame.event.Event) -> None:
        ...

    def update(self, dt: float) -> None:
        ...

    @abstractmethod
    def draw(self, screen: pygame.Surface) -> None:
        ...
