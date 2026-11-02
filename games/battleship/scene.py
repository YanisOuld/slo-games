"""BattleshipScene: the controller wiring model, views and AI. Only it mutates the model.

Touch-first input: a press on a ship starts a drag; a press released without
moving is a tap (rotate a ship / fire at a cell). No right click, no keyboard.
"""
from __future__ import annotations

import logging
import math
from dataclasses import dataclass

import pygame

from engine import constants as sc
from engine.scene import Scene
from engine.sidebar import Action, Sidebar, Stat
from engine.widget import Button
from games.icons import render_icon

from . import constants as k
from .ai import agent_for, heat_map
from .game import Gameplay
from .models import SIZE, Level, Phase, Shot, ShotResult
from .panels import Effect, GridView, draw_card, draw_fleet_status, draw_ship

log = logging.getLogger(__name__)


@dataclass
class Drag:
    index: int
    horizontal: bool
    grab: int                                   # which cell of the ship is under the finger
    origin: tuple[int, int, bool] | None        # where it sat on the grid (None = from the dock)
    start: tuple[int, int]
    moved: bool = False


class BattleshipScene(Scene):
    def __init__(self) -> None:
        self.game = Gameplay()
        self.level = Level.MEDIUM
        self.agent = agent_for(self.level, self.game.rng)
        self.show_heat = False
        self.time = 0.0

        self.sidebar = Sidebar(
            sc.SCREEN_HEIGHT, "Bataille navale", k.ACCENT,
            [Action("Nouvelle partie", self._new_game, "new"),
             Action("Niveau", self._next_level, "level", value=self.level.value),
             Action("Chaleur", self._toggle_heat, "radar", value="OFF"),
             Action("Retour au menu", self._back, "back")],
            icon=render_icon("Bataille navale", 44, k.ACCENT),
            sections=(("Comment jouer", (("Glisser", "placer un navire"),
                                         ("Toucher", "tourner un navire / tirer"),
                                         (None, "Coule toute la flotte ennemie"))),),
        )
        self.big = GridView(k.BIG_X, k.BIG_Y, k.BIG_CELL, labels=True)
        self.mini = GridView(k.SIDE_X, k.MINI_Y, k.MINI_CELL, labels=False)
        self.font_title = pygame.font.SysFont(None, 34)
        self.font_small = pygame.font.SysFont(None, 21)
        self.font_card = pygame.font.SysFont(None, 60)
        self.font_body = pygame.font.SysFont(None, 27)
        buttons_y = k.DOCK_Y + len(self.game.player.ships) * (k.DOCK_CELL + k.DOCK_GAP) + 12
        self.random_button = Button(k.SIDE_X, buttons_y, k.SIDE_W, 46, "Aléatoire",
                                    self.font_body, self._randomize)
        self.start_button = Button(k.SIDE_X, buttons_y + 56, k.SIDE_W, 46, "C'est parti !",
                                   self.font_body, self._start_battle,
                                   bg=(150, 86, 40), bg_hover=(190, 110, 52))
        self._reset_view()

    # -- buttons -----------------------------------------------------------------------

    def _reset_view(self) -> None:
        self.drag: Drag | None = None
        self.effects: list[tuple[GridView, Effect]] = []
        self.ai_timer = 0.0
        self.heat_enemy = self.heat_player = None
        self._say("Glisse tes navires sur la grille")

    def _new_game(self) -> None:
        self.game.new_game()
        self._reset_view()

    def _next_level(self) -> None:
        self.level = self.level.next()
        self.agent = agent_for(self.level, self.game.rng)
        self.sidebar.set_value(1, self.level.value)

    def _toggle_heat(self) -> None:
        self.show_heat = not self.show_heat
        self.sidebar.set_value(2, "ON" if self.show_heat else "OFF", on=self.show_heat)
        self._refresh_heat()

    def _randomize(self) -> None:
        if self.game.phase is Phase.PLACEMENT:
            self.game.player.randomize(self.game.rng)
            self._say("Flotte placée au hasard")

    def _start_battle(self) -> None:
        if self.game.phase is not Phase.PLACEMENT:
            return
        if not self.game.start_battle():
            self._say("Place tous tes navires", "error")
            return
        self._say("À toi de tirer !")
        self._refresh_heat()

    def _back(self) -> None:
        from games.menu.scene import MenuScene  # local import avoids circular import

        self.app.change_scene(MenuScene())

    def _say(self, message: str, kind: str = "info") -> None:
        self.message, self.kind = message, kind

    # -- placement (drag & drop) ---------------------------------------------------------

    def _dock_rect(self, index: int) -> pygame.Rect:
        ship = self.game.player.ships[index]
        return pygame.Rect(k.SIDE_X, k.DOCK_Y + index * (k.DOCK_CELL + k.DOCK_GAP),
                           ship.size * k.DOCK_CELL, k.DOCK_CELL)

    def _press_placement(self, pos: tuple[int, int]) -> None:
        board = self.game.player
        for i, ship in enumerate(board.ships):
            rect = self._dock_rect(i)
            if not ship.placed and rect.collidepoint(pos):
                self.drag = Drag(i, True, (pos[0] - rect.x) // k.DOCK_CELL, None, pos)
                return
        cell = self.big.cell_at(pos)
        index = board.ship_at(*cell) if cell else None
        if index is not None:
            ship = board.ships[index]
            grab = cell[0] - ship.x if ship.horizontal else cell[1] - ship.y
            self.drag = Drag(index, ship.horizontal, grab, (ship.x, ship.y, ship.horizontal), pos)
            board.remove(index)  # lifted off the grid while dragged

    def _drop_target(self, pos: tuple[int, int], drag: Drag) -> tuple[int, int] | None:
        cell = self.big.cell_at(pos)
        if cell is None:
            return None
        x, y = cell
        return (x - drag.grab, y) if drag.horizontal else (x, y - drag.grab)

    def _release_placement(self, pos: tuple[int, int]) -> None:
        drag, board = self.drag, self.game.player
        self.drag = None
        if not drag.moved:
            if drag.origin is not None:  # a tap on a placed ship: rotate it
                x, y, horizontal = drag.origin
                if not board.place(drag.index, x, y, not horizontal):
                    board.place(drag.index, x, y, horizontal)
                    self._say("Pas la place pour le tourner", "error")
            return
        target = self._drop_target(pos, drag)
        if target is not None and board.place(drag.index, *target, drag.horizontal):
            self._say("Prêt ? Touche « C'est parti ! »" if board.all_placed else "Glisse tes navires sur la grille")
        elif drag.origin is not None:
            board.place(drag.index, *drag.origin)  # invalid drop: back where it was

    # -- battle --------------------------------------------------------------------------

    def _tap_battle(self, pos: tuple[int, int]) -> None:
        cell = self.big.cell_at(pos)
        if cell is None or not self.game.player_turn:
            return
        shot = self.game.player_fire(*cell)
        if shot is None:
            return
        self._after_shot(shot, self.big, self.game.enemy, by_player=True)
        self.ai_timer = 0.0

    def _after_shot(self, shot: Shot, grid: GridView, board, by_player: bool) -> None:
        self.effects.append((grid, Effect(shot.x, shot.y, shot.result)))
        name = board.ships[shot.ship].name if shot.ship is not None else ""
        if by_player:
            self._say(*{ShotResult.MISS: ("Raté... l'IA vise", "info"),
                       ShotResult.HIT: ("Touché ! L'IA vise", "success"),
                       ShotResult.SUNK: (f"Coulé : {name} !", "success")}[shot.result])
        else:
            self._say(*{ShotResult.MISS: ("L'IA a raté. À toi !", "info"),
                       ShotResult.HIT: (f"L'IA a touché : {name}", "error"),
                       ShotResult.SUNK: (f"L'IA a coulé : {name}", "error")}[shot.result])
        if self.game.phase is Phase.OVER:
            won = self.game.winner_is_player
            self._say("Victoire !" if won else "Défaite...", "success" if won else "error")
        self._refresh_heat()

    def _refresh_heat(self) -> None:
        if not self.show_heat or self.game.phase is Phase.PLACEMENT:
            self.heat_enemy = self.heat_player = None
            return
        self.heat_enemy = self.big.make_heat(heat_map(self.game.enemy.view()))
        self.heat_player = self.mini.make_heat(heat_map(self.game.player.view()))

    # -- game loop -----------------------------------------------------------------------

    def handle_event(self, event: pygame.event.Event) -> None:
        self.sidebar.handle_event(event)
        placing = self.game.phase is Phase.PLACEMENT
        if placing:
            self.random_button.handle_event(event)
            if self.game.player.all_placed:
                self.start_button.handle_event(event)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if placing:
                self._press_placement(event.pos)
            elif self.game.phase is Phase.BATTLE:
                self._tap_battle(event.pos)
        elif event.type == pygame.MOUSEMOTION and self.drag is not None:
            if math.dist(event.pos, self.drag.start) > k.DRAG_THRESHOLD:
                self.drag.moved = True
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1 and self.drag is not None:
            self._release_placement(event.pos)

    def update(self, dt: float) -> None:
        self.time += dt
        for _, effect in self.effects:
            effect.age += dt
        self.effects = [(g, e) for g, e in self.effects if e.age < k.EFFECT_TIME]
        if self.game.phase is Phase.BATTLE and not self.game.player_turn:
            self.ai_timer += dt
            if self.ai_timer >= k.AI_DELAY:
                x, y = self.agent.choose(self.game.player.view())
                shot = self.game.ai_fire(x, y)
                if shot is not None:
                    self._after_shot(shot, self.mini, self.game.player, by_player=False)

    # -- drawing -------------------------------------------------------------------------

    def draw(self, screen: pygame.Surface) -> None:
        stats = self.game.stats["player"]
        sunk = sum(s.sunk for s in self.game.enemy.ships) if self.game.phase is not Phase.PLACEMENT else 0
        self.sidebar.draw(
            screen, f"Duel naval · {SIZE}×{SIZE}",
            [Stat("Tirs", str(stats.shots)), Stat("Précision", f"{stats.accuracy:.0%}"),
             Stat("Coulés", f"{sunk}/{len(self.game.enemy.ships)}")],
            self.message, self.kind,
        )
        if self.game.phase is Phase.PLACEMENT:
            self._draw_placement(screen)
        else:
            self._draw_battle(screen)

    def _title(self, screen: pygame.Surface, text: str, x: int) -> None:
        screen.blit(self.font_title.render(text, True, k.COLOR_TITLE), (x, 26))

    def _draw_placement(self, screen: pygame.Surface) -> None:
        board, drag = self.game.player, self.drag
        self._title(screen, "Place ta flotte", k.BIG_X)
        self.big.draw(screen, board, True, self.time, hidden=drag.index if drag else None)
        self._title(screen, "Navires", k.SIDE_X)
        for i, ship in enumerate(board.ships):
            rect = self._dock_rect(i)
            if ship.placed or (drag and drag.index == i):
                pygame.draw.rect(screen, k.COLOR_GRID, rect, 1, border_radius=rect.h // 2)
            else:
                draw_ship(screen, rect, True)
        self.random_button.draw(screen)
        if board.all_placed:
            self.start_button.draw(screen)
        help_text = self.font_small.render("Glisse un navire sur la grille · touche-le pour le tourner",
                                           True, k.COLOR_TEXT_DIM)
        screen.blit(help_text, (k.BIG_X, self.big.rect.bottom + 16))
        if drag is not None and drag.moved:
            self._draw_drag(screen, drag)

    def _draw_drag(self, screen: pygame.Surface, drag: Drag) -> None:
        pos = pygame.mouse.get_pos()
        size = self.game.player.ships[drag.index].size
        target = self._drop_target(pos, drag)
        if target is not None:
            valid = self.game.player.can_place(drag.index, *target, drag.horizontal)
            self.big.draw_ghost(screen, *target, size, drag.horizontal, valid)
        else:  # floating under the finger, off the grid
            c = k.BIG_CELL
            w, h = (size * c, c) if drag.horizontal else (c, size * c)
            off = drag.grab * c + c // 2
            rect = pygame.Rect(pos[0] - (off if drag.horizontal else c // 2),
                               pos[1] - (c // 2 if drag.horizontal else off), w, h)
            draw_ship(screen, rect, drag.horizontal, alpha=200)

    def _draw_battle(self, screen: pygame.Surface) -> None:
        g = self.game
        over = g.phase is Phase.OVER
        hover = None
        if g.player_turn and not over:
            cell = self.big.cell_at(pygame.mouse.get_pos())
            if cell is not None and cell not in g.enemy.shots:
                hover = cell
        self._title(screen, "Flotte ennemie", k.BIG_X)
        self.big.draw(screen, g.enemy, False, self.time, self.heat_enemy,
                      [e for grid, e in self.effects if grid is self.big], hover, reveal=over)
        draw_fleet_status(screen, g.enemy, k.BIG_X, self.big.rect.bottom + 20, 14, False, self.font_small)

        self._title(screen, "Ta flotte", k.SIDE_X)
        self.mini.draw(screen, g.player, True, self.time, self.heat_player,
                       [e for grid, e in self.effects if grid is self.mini])
        draw_fleet_status(screen, g.player, k.SIDE_X, self.mini.rect.bottom + 20, 11, True, self.font_small)
        if self.show_heat:
            self._draw_heat_legend(screen, self.mini.rect.bottom + 150)
        if over:
            self._draw_result(screen)

    def _draw_heat_legend(self, screen: pygame.Surface, y: int) -> None:
        bar = pygame.Rect(k.SIDE_X, y, k.SIDE_W, 10)
        for i in range(bar.w):
            t = i / bar.w
            color = tuple(int(a + (b - a) * t) for a, b in zip(k.COLOR_HEAT_COLD, k.COLOR_HEAT_HOT))
            pygame.draw.line(screen, color, (bar.x + i, bar.y), (bar.x + i, bar.bottom))
        for i, line in enumerate(("Chaleur : où un tireur malin", "pense trouver des navires")):
            text = self.font_small.render(line, True, k.COLOR_TEXT_DIM)
            screen.blit(text, (bar.x, bar.bottom + 8 + i * 18))

    def _draw_result(self, screen: pygame.Surface) -> None:
        g = self.game
        me, ai = g.stats["player"], g.stats["ai"]
        title = "Victoire !" if g.winner_is_player else "Défaite..."
        lines = [f"Toi : {me.shots} tirs · {me.accuracy:.0%} de précision",
                 f"IA ({self.level.value}) : {ai.shots} tirs · {ai.accuracy:.0%}",
                 "« Nouvelle partie » pour rejouer"]
        draw_card(screen, self.big.rect.center, title, lines, self.font_card, self.font_body)
