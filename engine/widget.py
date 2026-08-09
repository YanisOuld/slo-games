"""Reusable UI widgets: Widget (base), Label, Button.

Built on pygame.Rect (collidepoint, center...) and driven by handle_event(event)
so clicks, hover and keys share one uniform mechanism.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Callable

import pygame


class Widget(ABC):
    def __init__(self, x: int, y: int, width: int, height: int) -> None:
        self.rect = pygame.Rect(x, y, width, height)

    def handle_event(self, event: pygame.event.Event) -> None:
        ...

    @abstractmethod
    def draw(self, screen: pygame.Surface) -> None:
        ...


class Label(Widget):
    def __init__(
        self,
        x: int,
        y: int,
        text: str,
        font: pygame.font.Font,
        color: tuple[int, int, int] = (235, 235, 235),
    ) -> None:
        self.text = text
        self.font = font
        self.color = color
        super().__init__(x, y, *font.size(text))

    def set_text(self, text: str) -> None:
        self.text = text
        self.rect.size = self.font.size(text)

    def draw(self, screen: pygame.Surface) -> None:
        screen.blit(self.font.render(self.text, True, self.color), self.rect.topleft)


class Button(Widget):
    """Rectangular button; calls on_click on left click. Knows nothing of the game."""

    def __init__(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
        text: str,
        font: pygame.font.Font,
        on_click: Callable[[], None],
        bg: tuple[int, int, int] = (40, 40, 40),
        bg_hover: tuple[int, int, int] = (64, 64, 64),
        fg: tuple[int, int, int] = (235, 235, 235),
    ) -> None:
        super().__init__(x, y, width, height)
        self.text = text
        self.font = font
        self.on_click = on_click
        self.bg = bg
        self.bg_hover = bg_hover
        self.fg = fg

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.on_click()

    def draw(self, screen: pygame.Surface) -> None:
        hovered = self.rect.collidepoint(pygame.mouse.get_pos())
        pygame.draw.rect(screen, self.bg_hover if hovered else self.bg, self.rect)
        label = self.font.render(self.text, True, self.fg)
        screen.blit(label, label.get_rect(center=self.rect.center))
