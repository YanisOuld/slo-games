"""RunnerScene: the controller wiring model and views. Only it mutates the model."""
from __future__ import annotations

import logging
from enum import Enum

import pygame

from engine.scene import Scene

from . import constants as k
from .game import Gameplay
from .models import Action
from .panels import HudPanel, OverlayPanel, WorldView

log = logging.getLogger(__name__)

_JUMP_KEYS = (pygame.K_SPACE, pygame.K_UP, pygame.K_w, pygame.K_z)
_DUCK_KEYS = (pygame.K_DOWN, pygame.K_s)

# After dying, ignore jump presses briefly so a held jump doesn't instantly restart.
_RESTART_DELAY = 0.4


class _State(Enum):
    READY = "ready"
    PLAYING = "playing"
    PAUSED = "paused"
    OVER = "over"


class RunnerScene(Scene):
    def __init__(self) -> None:
        self.game = Gameplay()
        self.state = _State.READY
        self.step_timer = 0.0  # real seconds accumulated toward the next physics step
        self.over_timer = 0.0
        # Seconds since the current zone started: drives the banner and the sky fade.
        self.zone = self.game.zone
        self.zone_age = float("inf")

        self.world = WorldView()
        self.hud = HudPanel()
        self.start_overlay = OverlayPanel("Runner", (("Jouer", self._start), ("Retour au menu", self._back)))
        self.start_overlay.lines = [
            "Espace / Haut : sauter (maintenir = plus haut)",
            "Bas : se baisser (en l'air : tomber plus vite)",
        ]
        self.pause_overlay = OverlayPanel("Pause", (
            ("Reprendre", self._resume),
            ("Nouvelle partie", self._new_game),
            ("Retour au menu", self._back),
        ))
        self.over_overlay = OverlayPanel("Perdu !", (
            ("Rejouer", self._new_game),
            ("Retour au menu", self._back),
        ))

    # -- callbacks ---------------------------------------------------------------------

    def _start(self) -> None:
        self.state = _State.PLAYING
        self.step_timer = 0.0

    def _resume(self) -> None:
        self._start()

    def _new_game(self) -> None:
        self.game.reset()
        self.zone = self.game.zone
        self.zone_age = float("inf")
        self._start()

    def _back(self) -> None:
        from games.menu.scene import MenuScene  # local import avoids circular import

        self.app.change_scene(MenuScene())

    def _overlay(self) -> OverlayPanel | None:
        return {
            _State.READY: self.start_overlay,
            _State.PAUSED: self.pause_overlay,
            _State.OVER: self.over_overlay,
        }.get(self.state)

    @staticmethod
    def _held_action() -> Action:
        keys = pygame.key.get_pressed()
        if any(keys[key] for key in _JUMP_KEYS):
            return Action.JUMP
        if any(keys[key] for key in _DUCK_KEYS):
            return Action.DUCK
        return Action.NONE

    # -- game loop ---------------------------------------------------------------------

    def handle_event(self, event: pygame.event.Event) -> None:
        overlay = self._overlay()
        if overlay is not None:
            overlay.handle_event(event)
        if event.type != pygame.KEYDOWN:
            return
        if event.key == pygame.K_ESCAPE:
            if self.state is _State.PLAYING:
                self.state = _State.PAUSED
            elif self.state is _State.PAUSED:
                self._resume()
        elif event.key in _JUMP_KEYS:
            if self.state is _State.READY:
                self._start()
            elif self.state is _State.OVER and self.over_timer >= _RESTART_DELAY:
                self._new_game()

    def update(self, dt: float) -> None:
        if self.state is _State.OVER:
            self.over_timer += dt
            return
        if self.state is not _State.PLAYING:
            return
        self.zone_age += dt
        if self.game.zone != self.zone:
            self.zone = self.game.zone
            self.zone_age = 0.0
        # Fixed timestep: physics always advances in STEP_DT slices, whatever the FPS.
        self.step_timer += dt
        action = self._held_action()
        while self.step_timer >= k.STEP_DT:
            self.step_timer -= k.STEP_DT
            self.game.step(action)
            if self.game.game_over:
                self._on_game_over()
                break

    def _on_game_over(self) -> None:
        stats = self.game.statistics()
        self.state = _State.OVER
        self.over_timer = 0.0
        record = "  Nouveau record !" if stats.score >= stats.best and stats.score > 0 else ""
        self.over_overlay.lines = [
            f"Score : {stats.score}{record}",
            f"Zone {stats.zone}  ·  {stats.meters} m  ·  {stats.coins} pièces  ·  {stats.stomps} slimes",
        ]

    def draw(self, screen: pygame.Surface) -> None:
        self.world.draw(screen, self.game, self.zone_age)
        self.hud.draw(screen, self.game.statistics(), self.zone_age)
        overlay = self._overlay()
        if overlay is not None:
            overlay.draw(screen)
