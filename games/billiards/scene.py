"""BilliardsScene: the controller wiring model, views and AI. Only it mutates the model.

Touch input:
  - drag on the cloth: aim (the cue points from the cue ball toward your finger),
  - drag the power gauge down and let go: shoot (let go near the top to cancel),
  - ball in hand: drag the cue ball itself to place it.
"""
from __future__ import annotations

import logging
import math
from concurrent.futures import Future, ThreadPoolExecutor

import pygame

from engine import constants as sc
from engine.sidebar import Action, Sidebar, Stat
from engine.scene import Scene
from games.icons import render_icon

from . import constants as k
from . import physics
from .ai import BilliardsAI, PlannedShot
from .game import Gameplay
from .models import Level, Mode, Phase
from .panels import TableView, to_screen, to_table

log = logging.getLogger(__name__)

_NAMES = {Mode.VS_AI: ("Toi", "IA"), Mode.TWO_PLAYERS: ("Joueur 1", "Joueur 2")}


def _angle_lerp(a: float, b: float, t: float) -> float:
    diff = (b - a + math.pi) % (2 * math.pi) - math.pi
    return a + diff * t


class BilliardsScene(Scene):
    def __init__(self) -> None:
        self.mode = Mode.VS_AI
        self.level = Level.MEDIUM
        self.guide = True
        self.starter = 0
        self.view = TableView()
        self.executor = ThreadPoolExecutor(max_workers=1)
        self.sidebar = Sidebar(
            sc.SCREEN_HEIGHT, "Billard", k.ACCENT,
            [Action("Nouvelle partie", self._new_game, "new"),
             Action("Mode", self._next_mode, "ai", value=self.mode.value, value_on=True),
             Action("Niveau", self._next_level, "level", value=self.level.value),
             Action("Guide", self._toggle_guide, "radar", value="ON", value_on=True),
             Action("Retour au menu", self._back, "back")],
            icon=render_icon("Billard", 44, k.ACCENT),
            sections=(("Contrôles", (("Glisser", "sur le tapis : viser"),
                                     ("Jauge", "tirer vers le bas, lâcher"))),),
        )
        self._start()

    # -- setup / buttons -----------------------------------------------------------------

    def _start(self) -> None:
        self.game = Gameplay(_NAMES[self.mode])
        self.game.reset(starter=self.starter)
        self.angle = 0.0            # current aim (radians), toward the rack at first
        self.power = 0.0
        self.dragging: str | None = None   # "aim" | "power" | "cue"
        self.power_start_y = 0
        self.ai_future: Future[PlannedShot] | None = None
        self.ai_plan: PlannedShot | None = None
        self.ai_time = 0.0
        self.sinking: list[tuple[int, tuple[float, float], float]] = []
        self.on_table = {b.number for b in self.game.table.balls}
        self.message, self.kind = self._turn_message(), "info"

    def _new_game(self) -> None:
        self.starter = 1 - self.starter
        self._start()

    def _next_mode(self) -> None:
        self.mode = self.mode.next()
        self.sidebar.set_value(1, self.mode.value, on=True)
        self.starter = 0
        self._start()

    def _next_level(self) -> None:
        self.level = self.level.next()
        self.sidebar.set_value(2, self.level.value)

    def _toggle_guide(self) -> None:
        self.guide = not self.guide
        self.sidebar.set_value(3, "ON" if self.guide else "OFF", on=self.guide)

    def _back(self) -> None:
        from games.menu.scene import MenuScene  # local import avoids circular import

        self.executor.shutdown(wait=False, cancel_futures=True)
        self.app.change_scene(MenuScene())

    # -- turn logic ----------------------------------------------------------------------

    def _ai_turn(self) -> bool:
        return self.mode is Mode.VS_AI and self.game.current == 1

    def _human_can_act(self) -> bool:
        return self.game.phase is Phase.AIMING and not self._ai_turn()

    def _turn_message(self) -> str:
        g = self.game
        if self._ai_turn():
            return "L'IA réfléchit..."
        who = "À toi" if self.mode is Mode.VS_AI else f"À {g.shooter.name}"
        return f"{who} : bille en main" if g.ball_in_hand else f"{who} de jouer"

    def _shoot(self, angle: float, power: float) -> None:
        self.angle = angle
        if self.game.shoot(angle, power):
            self.message, self.kind = "...", "info"
        self.power = 0.0

    # -- input ---------------------------------------------------------------------------

    def handle_event(self, event: pygame.event.Event) -> None:
        self.sidebar.handle_event(event)
        if not self._human_can_act():
            return
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self._press(event.pos)
        elif event.type == pygame.MOUSEMOTION and self.dragging:
            self._drag(event.pos)
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1 and self.dragging:
            if self.dragging == "power" and self.power >= k.MIN_POWER:
                self._shoot(self.angle, self.power)
            self.power = 0.0 if self.dragging == "power" else self.power
            self.dragging = None

    def _press(self, pos: tuple[int, int]) -> None:
        bar = pygame.Rect(k.BAR_X - 10, k.PLAY_Y - 10, k.BAR_W + 20, int(physics.H) + 20)
        cue = self.game.table.cue
        table_rect = pygame.Rect(k.PLAY_X, k.PLAY_Y, int(physics.W), int(physics.H))
        if bar.collidepoint(pos):
            self.dragging, self.power_start_y = "power", pos[1]
        elif self.game.ball_in_hand and math.dist(pos, to_screen(cue.x, cue.y)) < 3 * physics.R:
            self.dragging = "cue"
        elif table_rect.inflate(2 * k.RAIL, 2 * k.RAIL).collidepoint(pos):
            self.dragging = "aim"
            self._drag(pos)

    def _drag(self, pos: tuple[int, int]) -> None:
        cue = self.game.table.cue
        if self.dragging == "power":
            self.power = max(0.0, min(1.0, (pos[1] - self.power_start_y) / (physics.H - 8)))
        elif self.dragging == "cue":
            self.game.place_cue(*to_table(*pos))   # refused (kept in place) if not a free spot
        elif self.dragging == "aim":
            x, y = to_table(*pos)
            if math.hypot(x - cue.x, y - cue.y) > 4:
                self.angle = math.atan2(y - cue.y, x - cue.x)

    # -- game loop -----------------------------------------------------------------------

    def update(self, dt: float) -> None:
        self.sinking = [(n, p, age + dt) for n, p, age in self.sinking if age + dt < k.POT_ANIM]
        g = self.game
        if g.phase is Phase.ROLLING:
            ended = g.update(dt)
            self._track_pockets()
            if ended:
                self.message, self.kind = g.last_outcome.text, g.last_outcome.kind
                if g.phase is not Phase.OVER and g.last_outcome.kind == "info":
                    self.message = f"{g.last_outcome.text} · {self._turn_message()}"
                elif g.phase is Phase.OVER and self.mode is Mode.VS_AI:   # from the human's side
                    won = g.winner == 0
                    self.message, self.kind = ("Tu as gagné !", "success") if won else ("L'IA a gagné...", "error")
        elif g.phase is Phase.AIMING and self._ai_turn():
            self._update_ai(dt)

    def _track_pockets(self) -> None:
        """Start the sinking animation for balls that just dropped."""
        for ball in self.game.table.balls:
            if ball.pocketed and ball.number in self.on_table:
                self.on_table.discard(ball.number)
                pocket = min(physics.POCKETS, key=lambda p: math.dist(p, (ball.x, ball.y)))
                self.sinking.append((ball.number, pocket, 0.0))
            elif not ball.pocketed:
                self.on_table.add(ball.number)

    def _update_ai(self, dt: float) -> None:
        """AI turn: think (in a worker thread), place the cue ball if in hand, swing the
        cue to its angle, pull back to its power, shoot."""
        if self.ai_plan is None:
            if self.ai_future is None:
                self.ai_future = self.executor.submit(BilliardsAI(self.level, self.game.rng).plan, self.game)
                self.ai_time = 0.0
                self.ai_start_angle = self.angle
                self.message, self.kind = "L'IA réfléchit...", "info"
            self.ai_time += dt
            if self.ai_future.done() and self.ai_time >= k.AI_THINK:
                self.ai_plan, self.ai_future, self.ai_time = self.ai_future.result(), None, 0.0
                if self.ai_plan.cue_pos:
                    self.game.place_cue(*self.ai_plan.cue_pos)
                self.message = "L'IA vise..."
            return
        self.ai_time += dt
        plan = self.ai_plan
        aim_t = min(1.0, self.ai_time / k.AI_AIM_TIME)
        self.angle = _angle_lerp(self.ai_start_angle, plan.angle, aim_t * aim_t * (3 - 2 * aim_t))
        charge = max(0.0, self.ai_time - k.AI_AIM_TIME) / k.AI_CHARGE_TIME
        self.power = plan.power * min(1.0, charge)
        if charge >= 1.0:
            self.ai_plan = None
            self._shoot(plan.angle, plan.power)

    # -- drawing -------------------------------------------------------------------------

    def draw(self, screen: pygame.Surface) -> None:
        g = self.game
        labels = ("Toi", "IA") if self.mode is Mode.VS_AI else ("J1", "J2")
        left = [len(g.remaining(p.group)) if p.group else 7 for p in g.players]
        self.sidebar.draw(
            screen, "Billard américain · 8-ball",
            [Stat(labels[0], str(left[0])), Stat(labels[1], str(left[1])), Stat("Coups", str(g.shots))],
            self.message, self.kind,
        )
        self.view.draw_players(screen, g, g.ball_in_hand)
        self.view.draw_table(screen, g, self.sinking)
        aiming = g.phase is Phase.AIMING
        if aiming and (not self._ai_turn() or self.ai_plan is not None):
            screen.set_clip(pygame.Rect(k.NAV_WIDTH, 0, sc.SCREEN_WIDTH - k.NAV_WIDTH, sc.SCREEN_HEIGHT))
            self.view.draw_aim(screen, g, self.angle, self.power, self.guide and not self._ai_turn())
            screen.set_clip(None)   # the cue never draws over the sidebar
        self.view.draw_power_bar(screen, self.power, aiming and not self._ai_turn())
        if aiming and g.ball_in_hand and not self._ai_turn():
            cue = g.table.cue
            pygame.draw.circle(screen, k.ACCENT, to_screen(cue.x, cue.y), int(physics.R) + 5, 2)
        if g.phase is Phase.OVER:
            self._draw_result(screen)

    def _draw_result(self, screen: pygame.Surface) -> None:
        g = self.game
        if self.mode is Mode.VS_AI:
            title = "Victoire !" if g.winner == 0 else "Défaite..."
        else:
            title = f"{g.players[g.winner].name} gagne !"
        self.view.draw_result(screen, title, [g.last_outcome.text, f"{g.shots} coups joués",
                                              "« Nouvelle partie » pour rejouer"])
