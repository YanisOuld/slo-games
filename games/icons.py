"""Game icons drawn with pygame primitives (no image files).

Shared by the menu cards and the games' sidebars. A game with no icon here gets
a generic "play" triangle.
"""
from __future__ import annotations

from typing import Callable

import pygame

Color = tuple[int, int, int]


def _icon_binairo(s: pygame.Surface, r: pygame.Rect, accent: Color) -> None:
    pattern = ("1010", "0101", "1100", "0011")
    cell = min(r.w, r.h) // 5
    ox, oy = r.centerx - 2 * cell, r.centery - 2 * cell
    for y, row in enumerate(pattern):
        for x, v in enumerate(row):
            center = (ox + x * cell + cell // 2, oy + y * cell + cell // 2)
            if v == "1":
                pygame.draw.circle(s, accent, center, cell // 2 - 4)
            else:
                pygame.draw.circle(s, (230, 230, 240), center, cell // 2 - 4, 3)


def _icon_snake(s: pygame.Surface, r: pygame.Rect, accent: Color) -> None:
    cell = min(r.w, r.h) // 6
    ox, oy = r.centerx - 3 * cell, r.centery - 3 * cell
    path = [(1, 4), (2, 4), (3, 4), (4, 4), (4, 3), (4, 2), (3, 2), (2, 2)]
    for i, (x, y) in enumerate(path):
        shade = tuple(max(0, c - i * 12) for c in accent)
        pygame.draw.rect(s, shade, (ox + x * cell + 2, oy + y * cell + 2, cell - 4, cell - 4),
                         border_radius=5)
    hx, hy = path[-1]
    pygame.draw.circle(s, (20, 20, 20), (ox + hx * cell + cell // 3, oy + hy * cell + cell // 3), 3)
    pygame.draw.circle(s, (220, 70, 80), (ox + 2 * cell - cell // 2 + cell, oy + cell + cell // 2), cell // 3)


def _icon_minesweeper(s: pygame.Surface, r: pygame.Rect, accent: Color) -> None:
    cell = min(r.w, r.h) // 4
    ox, oy = r.centerx - int(1.5 * cell), r.centery - int(1.5 * cell)
    font = pygame.font.SysFont(None, int(cell * 0.9), bold=True)
    grid = ("1F ", "12 ", "M1 ")
    numbers = {"1": (100, 160, 255), "2": (100, 210, 120)}
    for y, row in enumerate(grid):
        for x, v in enumerate(row):
            rect = pygame.Rect(ox + x * cell + 2, oy + y * cell + 2, cell - 4, cell - 4)
            hidden = v in " F"
            pygame.draw.rect(s, (70, 78, 98) if hidden else (44, 46, 58), rect, border_radius=4)
            if v in numbers:
                label = font.render(v, True, numbers[v])
                s.blit(label, label.get_rect(center=rect.center))
            elif v == "F":
                px = rect.x + rect.w * 2 // 5
                pygame.draw.line(s, (230, 230, 230), (px, rect.y + 8), (px, rect.bottom - 8), 2)
                pygame.draw.polygon(s, accent, [(px, rect.y + 8), (rect.right - 8, rect.y + 14),
                                                (px, rect.y + 20)])
            elif v == "M":
                pygame.draw.rect(s, accent, rect, border_radius=4)
                pygame.draw.circle(s, (15, 15, 15), rect.center, cell // 4)


def _icon_runner(s: pygame.Surface, r: pygame.Rect, accent: Color) -> None:
    ground = r.bottom - 28
    pygame.draw.rect(s, (60, 46, 52), (r.x, ground, r.w, r.bottom - ground),
                     border_bottom_left_radius=10, border_bottom_right_radius=10)
    pygame.draw.rect(s, (96, 200, 120), (r.x, ground, r.w, 6))
    body = pygame.Rect(r.x + 36, ground - 62, 30, 40)  # mid-jump
    pygame.draw.rect(s, (90, 190, 250), body, border_radius=7)
    pygame.draw.circle(s, (250, 250, 250), (body.right - 8, body.y + 11), 5)
    pygame.draw.circle(s, (20, 20, 30), (body.right - 6, body.y + 11), 2)
    pygame.draw.rect(s, (200, 120, 70), (r.x + 92, ground - 30, 28, 30), border_radius=3)
    for i in range(3):
        pygame.draw.circle(s, accent, (r.x + 82 + i * 20, ground - 62 + abs(i - 1) * 8), 6)
    drone = pygame.Rect(r.right - 56, ground - 70, 36, 16)
    pygame.draw.rect(s, (240, 170, 90), drone, border_radius=6)
    pygame.draw.circle(s, (240, 70, 80), drone.center, 3)


def _icon_connect4(s: pygame.Surface, r: pygame.Rect, accent: Color) -> None:
    cols, rows = 5, 4
    cell = min(r.w // (cols + 1), r.h // (rows + 1))
    board = pygame.Rect(0, 0, cell * cols + 12, cell * rows + 12)
    board.center = r.center
    pygame.draw.rect(s, tuple(int(c * 0.55) for c in accent), board, border_radius=12)
    discs = {(1, 3): (240, 100, 100), (2, 3): (250, 210, 70), (2, 2): (240, 100, 100),
             (3, 3): (250, 210, 70), (3, 2): (250, 210, 70), (3, 1): (240, 100, 100),
             (4, 3): (240, 100, 100), (1, 2): (250, 210, 70)}
    for c in range(cols):
        for row in range(rows):
            center = (board.x + 6 + c * cell + cell // 2, board.y + 6 + row * cell + cell // 2)
            pygame.draw.circle(s, discs.get((c, row), (20, 22, 32)), center, int(cell * 0.38))


def _icon_generic(s: pygame.Surface, r: pygame.Rect, accent: Color) -> None:
    pygame.draw.polygon(s, accent, [(r.centerx - 22, r.centery - 28), (r.centerx - 22, r.centery + 28),
                                    (r.centerx + 30, r.centery)])


_ICONS: dict[str, Callable[[pygame.Surface, pygame.Rect, Color], None]] = {
    "Binairo": _icon_binairo,
    "Snake": _icon_snake,
    "Démineur": _icon_minesweeper,
    "Runner": _icon_runner,
    "Puissance 4": _icon_connect4,
}


def draw_icon(name: str, surface: pygame.Surface, rect: pygame.Rect, accent: Color) -> None:
    _ICONS.get(name, _icon_generic)(surface, rect, accent)


def render_icon(name: str, size: int, accent: Color) -> pygame.Surface:
    """The icon on a transparent square of the given size (drawn big, scaled down smoothly)."""
    big = pygame.Surface((160, 160), pygame.SRCALPHA)
    draw_icon(name, big, big.get_rect(), accent)
    return pygame.transform.smoothscale(big, (size, size))
