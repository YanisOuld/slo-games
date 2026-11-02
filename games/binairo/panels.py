"""Binairo views. They draw and report clicks via callbacks; they never mutate the model."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import pygame

from engine.widget import Widget

from . import constants as k
from .game import Gameplay
from .models import BoxType, Hint, HintType

Color = tuple[int, int, int]

_TILE_COLORS = {BoxType.WHITE: k.COLOR_WHITE, BoxType.BLACK: k.COLOR_BLACK}
_SUPERSAMPLE = 4


def _darker(color: Color, factor: float = 0.72) -> Color:
    return tuple(int(c * factor) for c in color)


@dataclass
class BoardState:
    """Everything the board shows, derived from the model once per frame by the Scene."""

    game: Gameplay
    triplets: set[tuple[int, int]]
    broken_hints: list[Hint]
    solved: bool
    elapsed: float


class BoardPanel(Widget):
    def __init__(self, rect: pygame.Rect, size: int,
                 on_cell_click: Callable[[int, int, bool], None]) -> None:
        super().__init__(rect.x, rect.y, rect.width, rect.height)
        self.size = size
        self.on_cell_click = on_cell_click

        usable = rect.height - 2 * k.PADDING - k.COUNTER_MARGIN - 2 * k.FRAME_PAD
        self.box = usable // size
        self.board_px = self.box * size
        total = self.board_px + 2 * k.FRAME_PAD + k.COUNTER_MARGIN
        # Center frame + counters inside the panel.
        self.ox = rect.x + (rect.width - total) // 2 + k.FRAME_PAD
        self.oy = rect.y + (rect.height - total) // 2 + k.FRAME_PAD
        self.frame = pygame.Rect(self.ox - k.FRAME_PAD, self.oy - k.FRAME_PAD,
                                 self.board_px + 2 * k.FRAME_PAD, self.board_px + 2 * k.FRAME_PAD)
        self.radius = max(4, self.box // 4)
        self._sprites: dict[tuple, pygame.Surface] = {}

        self.font_counter = pygame.font.SysFont(None, 19)
        self.font_win = pygame.font.SysFont(None, 84)
        self.font_win_sub = pygame.font.SysFont(None, 30)

    def cell_at(self, pos: tuple[int, int]) -> tuple[int, int] | None:
        x, y = pos[0] - self.ox, pos[1] - self.oy
        if 0 <= x < self.board_px and 0 <= y < self.board_px:
            return x // self.box, y // self.box
        return None

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type != pygame.MOUSEBUTTONDOWN or event.button not in (1, 3):
            return
        cell = self.cell_at(event.pos)
        if cell is not None:
            self.on_cell_click(*cell, event.button == 3)

    # -- drawing -----------------------------------------------------------------------

    def draw(self, screen: pygame.Surface, state: BoardState) -> None:
        hovered = None if state.solved else self.cell_at(pygame.mouse.get_pos())
        pygame.draw.rect(screen, k.COLOR_FRAME, self.frame, border_radius=14)
        pygame.draw.rect(screen, k.COLOR_FRAME_BORDER, self.frame, width=1, border_radius=14)
        self._draw_cells(screen, state, hovered)
        self._draw_hints(screen, state)
        self._draw_counters(screen, state, hovered)
        if state.solved:
            self._draw_win(screen, state.elapsed)

    def _cell_rect(self, c: int, r: int) -> pygame.Rect:
        return pygame.Rect(self.ox + c * self.box + k.CELL_GAP, self.oy + r * self.box + k.CELL_GAP,
                           self.box - 2 * k.CELL_GAP, self.box - 2 * k.CELL_GAP)

    def _draw_cells(self, screen: pygame.Surface, state: BoardState,
                    hovered: tuple[int, int] | None) -> None:
        grid = state.game.player_game
        for c in range(self.size):
            for r in range(self.size):
                box = grid[c][r]
                pos = self._cell_rect(c, r).topleft
                if box.type is BoxType.NONE:
                    focus = hovered is not None and (c == hovered[0] or r == hovered[1])
                    screen.blit(self._sprite("focus" if focus else "empty"), pos)
                else:
                    screen.blit(self._sprite("given" if box.is_blocked else "placed", box.type), pos)
                if (c, r) in state.triplets:
                    screen.blit(self._sprite("ring", k.COLOR_ERROR), (pos[0] - 1, pos[1] - 1))
                elif (c, r) == hovered and not box.is_blocked:
                    screen.blit(self._sprite("ring", k.COLOR_HOVER), (pos[0] - 1, pos[1] - 1))

    def _draw_hints(self, screen: pygame.Surface, state: BoardState) -> None:
        grid = state.game.player_game
        for h in state.game.hints:
            c1, c2 = h.coord1, h.coord2
            if h.direction.is_horizontal():
                cx, cy = self.ox + max(c1.x, c2.x) * self.box, self.oy + (c1.y + 0.5) * self.box
            else:
                cx, cy = self.ox + (c1.x + 0.5) * self.box, self.oy + max(c1.y, c2.y) * self.box
            if h in state.broken_hints:
                look = "broken"
            elif BoxType.NONE not in (grid[c1.x][c1.y].type, grid[c2.x][c2.y].type):
                look = "done"   # both cells filled and the hint holds: fade it out
            else:
                look = "open"
            sprite = self._sprite("hint", h.type, look)
            screen.blit(sprite, sprite.get_rect(center=(int(cx), int(cy))))

    # -- sprites: drawn 4x bigger then smoothly scaled down, for anti-aliased edges --

    def _sprite(self, *key) -> pygame.Surface:
        if key not in self._sprites:
            self._sprites[key] = self._render(*key)
        return self._sprites[key]

    def _render(self, kind: str, *args) -> pygame.Surface:
        ss = _SUPERSAMPLE
        tile = self.box - 2 * k.CELL_GAP
        size = tile + 2 if kind == "ring" else tile
        if kind == "hint":
            size = 2 * max(6, int(self.box * 0.26))
        big = pygame.Surface((size * ss, size * ss), pygame.SRCALPHA)
        rect = big.get_rect()
        radius = self.radius * ss
        if kind in ("empty", "focus"):
            pygame.draw.rect(big, k.COLOR_EMPTY_FOCUS if kind == "focus" else k.COLOR_EMPTY, rect,
                             border_radius=radius)
        elif kind == "placed":
            # Raised tile: darker bottom edge under a slightly shorter face.
            color = _TILE_COLORS[args[0]]
            pygame.draw.rect(big, _darker(color), rect, border_radius=radius)
            pygame.draw.rect(big, color, (0, 0, rect.w, rect.h - k.BEVEL * ss), border_radius=radius)
        elif kind == "given":
            # Flat tile with an engraved dot: fixed from the start, can't be changed.
            color = _TILE_COLORS[args[0]]
            pygame.draw.rect(big, color, rect, border_radius=radius)
            pygame.draw.circle(big, _darker(color, 0.82), rect.center, int(rect.w * 0.16))
        elif kind == "ring":
            pygame.draw.rect(big, args[0], rect, width=2 * ss, border_radius=radius + ss)
        elif kind == "hint":
            hint_type, look = args
            bg, fg = {"open": (k.COLOR_HINT_BG, k.COLOR_HINT),
                      "done": (k.COLOR_EMPTY, k.COLOR_STAT),
                      "broken": (k.COLOR_ERROR, k.COLOR_TEXT)}[look]
            c = rect.w // 2
            pygame.draw.circle(big, bg, (c, c), c)
            s, w = int(c * 0.45), max(ss, int(c * 0.22))
            if hint_type is HintType.EQUAL:
                for dy in (-int(c * 0.22), int(c * 0.22)):
                    pygame.draw.line(big, fg, (c - s, c + dy), (c + s, c + dy), w)
            else:
                pygame.draw.line(big, fg, (c - s, c - s), (c + s, c + s), w)
                pygame.draw.line(big, fg, (c - s, c + s), (c + s, c - s), w)
        sprite = pygame.transform.smoothscale(big, (size, size))
        if kind == "hint" and args[1] == "done":
            sprite.set_alpha(110)
        return sprite

    def _draw_counters(self, screen: pygame.Surface, state: BoardState,
                       hovered: tuple[int, int] | None) -> None:
        """Per line: whites and blues still to place, or a check mark once the line is valid."""
        stats = state.game.statistics()
        half = self.size // 2
        bad_cols = {c for c, _ in state.triplets}
        bad_rows = {r for _, r in state.triplets}
        below = self.frame.bottom + k.COUNTER_MARGIN // 2
        right = self.frame.right + k.COUNTER_MARGIN // 2
        for c in range(self.size):
            white, black, _ = stats.per_col[c]
            cx = self.ox + c * self.box + self.box // 2
            focus = hovered is not None and hovered[0] == c
            self._counter(screen, (cx, below), half - white, half - black, c in bad_cols, focus, vertical=True)
        for r in range(self.size):
            white, black, _ = stats.per_row[r]
            cy = self.oy + r * self.box + self.box // 2
            focus = hovered is not None and hovered[1] == r
            self._counter(screen, (right, cy), half - white, half - black, r in bad_rows, focus, vertical=False)

    def _counter(self, screen: pygame.Surface, center: tuple[int, int], left_white: int,
                 left_black: int, has_triplet: bool, focus: bool, vertical: bool) -> None:
        cx, cy = center
        if focus:
            pill = pygame.Rect(0, 0, self.box - 2, 34) if vertical else pygame.Rect(0, 0, 34, self.box - 2)
            pill.center = center
            pygame.draw.rect(screen, k.COLOR_EMPTY, pill, border_radius=8)
        if left_white == 0 and left_black == 0 and not has_triplet:
            pygame.draw.lines(screen, k.COLOR_DONE, False,
                              [(cx - 6, cy), (cx - 2, cy + 4), (cx + 6, cy - 5)], 3)
            return
        offsets = ((0, -8), (0, 8)) if vertical else ((-10, 0), (10, 0))
        for (dx, dy), left, color in zip(offsets, (left_white, left_black), (k.COLOR_WHITE, k.COLOR_BLACK)):
            if left < 0 or has_triplet:
                color = k.COLOR_ERROR
            label = self.font_counter.render(str(left), True, color if focus or left else k.COLOR_STAT)
            screen.blit(label, label.get_rect(center=(cx + dx, cy + dy)))

    def _draw_win(self, screen: pygame.Surface, elapsed: float) -> None:
        shade = pygame.Surface(self.frame.size, pygame.SRCALPHA)
        pygame.draw.rect(shade, k.COLOR_SHADE, shade.get_rect(), border_radius=14)
        screen.blit(shade, self.frame.topleft)
        cx, cy = self.frame.center
        title = self.font_win.render("Bravo !", True, k.COLOR_TEXT)
        screen.blit(title, title.get_rect(center=(cx, cy - 24)))
        pygame.draw.rect(screen, k.ACCENT, (cx - 30, cy + 14, 60, 4), border_radius=2)
        minutes, seconds = divmod(int(elapsed), 60)
        sub = self.font_win_sub.render(f"Grille résolue en {minutes:02d}:{seconds:02d}", True, k.COLOR_TEXT_SOFT)
        screen.blit(sub, sub.get_rect(center=(cx, cy + 46)))
