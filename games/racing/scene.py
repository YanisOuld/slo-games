"""RacingScene: the controller wiring model and views. Only it mutates the model."""
from __future__ import annotations

import logging

import pygame

from engine import constants as sc
from engine.scene import Scene
from engine.sidebar import Action, Sidebar, Stat
from games.icons import render_icon

from . import constants as k
from .game import Gameplay
from .models import Controls, LapRecord
from .panels import TrackView, format_time
from .tracks import TRACKS, Track

log = logging.getLogger(__name__)

_UP = (pygame.K_UP, pygame.K_z, pygame.K_w)
_DOWN = (pygame.K_DOWN, pygame.K_s)
_LEFT = (pygame.K_LEFT, pygame.K_q, pygame.K_a)
_RIGHT = (pygame.K_RIGHT, pygame.K_d)
_GO_FLASH = 0.7     # seconds "GO !" stays up
_POPUP_TIME = 1.6   # seconds a lap time floats over the track
_KMH = 0.6          # px/s -> displayed km/h (for fun)


def _held(keys, group: tuple[int, ...]) -> bool:
    return any(keys[key] for key in group)


class RacingScene(Scene):
    # Kept across visits: best lap (and its ghost) per track, and the last track picked.
    _records: dict[str, LapRecord] = {}
    _track_index = 0

    def __init__(self) -> None:
        self.show_ghost = True
        self.show_sensors = False
        self.sidebar = Sidebar(
            sc.SCREEN_HEIGHT, "Course", k.ACCENT,
            [Action("Recommencer", self._restart, "new"),
             Action("Circuit", self._next_track, "flag", value=""),
             Action("Fantôme", self._toggle_ghost, "ghost", value="ON", value_on=True),
             Action("Capteurs", self._toggle_sensors, "radar", value="OFF"),
             Action("Retour au menu", self._back, "back")],
            icon=render_icon("Course", 44, k.ACCENT),
            sections=(("Contrôles", (("Flèches", "conduire (ou ZQSD)"),
                                     ("Espace", "frein à main : drift !"))),),
        )
        self._load_track()

    # -- setup -------------------------------------------------------------------------

    def _load_track(self) -> None:
        spec = TRACKS[RacingScene._track_index]
        track = Track(spec, k.VIEW_W - 2 * k.VIEW_MARGIN, k.VIEW_H - 2 * k.VIEW_MARGIN)
        self.game = Gameplay(track, RacingScene._records.get(spec.name))
        self.view = TrackView(pygame.Rect(k.VIEW_X, 0, k.VIEW_W, k.VIEW_H), track)
        self.sidebar.set_value(1, spec.name)
        self._restart()

    def _restart(self) -> None:
        self.game.reset()
        self.view.clear_skids()
        self.countdown = k.COUNTDOWN
        self.go_flash = 0.0
        self.step_timer = 0.0
        self.popup: tuple[str, float] | None = None
        self.laps_seen = 0

    # -- buttons -----------------------------------------------------------------------

    def _next_track(self) -> None:
        RacingScene._track_index = (RacingScene._track_index + 1) % len(TRACKS)
        self._load_track()

    def _toggle_ghost(self) -> None:
        self.show_ghost = not self.show_ghost
        self.sidebar.set_value(2, "ON" if self.show_ghost else "OFF", on=self.show_ghost)

    def _toggle_sensors(self) -> None:
        self.show_sensors = not self.show_sensors
        self.sidebar.set_value(3, "ON" if self.show_sensors else "OFF", on=self.show_sensors)

    def _back(self) -> None:
        from games.menu.scene import MenuScene  # local import avoids circular import

        self.app.change_scene(MenuScene())

    # -- game loop ---------------------------------------------------------------------

    def handle_event(self, event: pygame.event.Event) -> None:
        self.sidebar.handle_event(event)
        if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
            self._restart()

    @staticmethod
    def _controls() -> Controls:
        keys = pygame.key.get_pressed()
        return Controls(
            throttle=_held(keys, _UP) - _held(keys, _DOWN),
            steer=_held(keys, _RIGHT) - _held(keys, _LEFT),
            handbrake=keys[pygame.K_SPACE],
        )

    def update(self, dt: float) -> None:
        if self.popup is not None:
            text, age = self.popup
            self.popup = (text, age + dt) if age + dt < _POPUP_TIME else None
        if self.countdown > 0:
            self.countdown -= dt
            if self.countdown <= 0:
                self.go_flash = _GO_FLASH
            return
        self.go_flash = max(0.0, self.go_flash - dt)
        if self.game.finished:
            return
        # Fixed timestep: physics always advances in STEP_DT slices, whatever the FPS.
        self.step_timer += dt
        controls = self._controls()
        while self.step_timer >= k.STEP_DT and not self.game.finished:
            self.step_timer -= k.STEP_DT
            self.game.step(controls)
            self.view.mark_skids(self.game)
        self._check_lap()

    def _check_lap(self) -> None:
        g = self.game
        if len(g.lap_times) == self.laps_seen:
            return
        self.laps_seen = len(g.lap_times)
        lap_time = format_time(g.lap_times[-1])
        if g.new_best:
            RacingScene._records[self.game.track.name] = g.best
        self.popup = (f"Record ! {lap_time}" if g.new_best else f"Tour {self.laps_seen}   {lap_time}", 0.0)

    def _message(self) -> tuple[str, str]:
        g = self.game
        if g.finished:
            return f"Arrivée en {format_time(g.time)}", "success"
        if self.countdown > 0:
            return "Prêt ?", "info"
        if g.touching_wall:
            return "Aïe, le mur !", "error"
        return f"{int(g.speed * _KMH)} km/h", "info"

    def draw(self, screen: pygame.Surface) -> None:
        stats = self.game.statistics()
        spec = TRACKS[RacingScene._track_index]
        message, kind = self._message()
        self.sidebar.draw(
            screen, f"Circuit {RacingScene._track_index + 1}/{len(TRACKS)} · {spec.level}",
            [Stat("Tour", f"{stats.lap}/{stats.laps}"), Stat("Temps", format_time(stats.lap_time)),
             Stat("Record", format_time(stats.best_lap))],
            message, kind,
        )
        self.view.draw(screen, self.game, self.show_ghost, self.show_sensors,
                       self.countdown, self.go_flash, self.popup)
