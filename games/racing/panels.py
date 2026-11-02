"""Racing views. They draw only; they never mutate the model (input lives in the Scene)."""
from __future__ import annotations

import math

import pygame

from engine.widget import Widget

from . import constants as k
from .game import Gameplay
from .tracks import Track

Color = tuple[int, int, int]
_SUPERSAMPLE = 2
_CAR_SCALE = 3          # car sprite drawn 3x, then rotozoomed down (smooth edges)
_KERB_CURVE = 0.07      # curvature above which the edge gets red/white kerbs


def format_time(seconds: float | None) -> str:
    if seconds is None:
        return "--"
    minutes, rest = divmod(seconds, 60)
    return f"{int(minutes)}:{rest:05.2f}"


def _lerp(a: Color, b: Color, t: float) -> Color:
    return tuple(int(x + (y - x) * t) for x, y in zip(a, b))


class TrackView(Widget):
    def __init__(self, rect: pygame.Rect, track: Track) -> None:
        super().__init__(rect.x, rect.y, rect.w, rect.h)
        self.track = track
        self.origin = (rect.x + k.VIEW_MARGIN, rect.y + k.VIEW_MARGIN)  # world (0, 0) on screen
        self.base = self._render_track()
        self.skids = pygame.Surface(rect.size, pygame.SRCALPHA)
        self.car_sprite = self._render_car(k.COLOR_CAR, k.COLOR_CAR_DARK)
        self.ghost_sprite = self._render_car(k.COLOR_GHOST, (150, 155, 175))
        self.ghost_sprite.set_alpha(95)
        self.font_big = pygame.font.SysFont(None, 150)
        self.font_title = pygame.font.SysFont(None, 64)
        self.font_body = pygame.font.SysFont(None, 28)
        self.font_popup = pygame.font.SysFont(None, 40)

    def to_screen(self, x: float, y: float) -> tuple[int, int]:
        return int(self.origin[0] + x), int(self.origin[1] + y)

    def clear_skids(self) -> None:
        self.skids.fill((0, 0, 0, 0))

    def mark_skids(self, game: Gameplay) -> None:
        """Called after each physics step: rear tyres leave marks while drifting."""
        if not game.drifting:
            return
        car = game.car
        fx, fy = math.cos(car.angle), math.sin(car.angle)
        rx, ry = -fy, fx
        for side in (-1, 1):
            wx = car.x - fx * k.CAR_LENGTH * 0.35 + rx * side * k.CAR_WIDTH * 0.4
            wy = car.y - fy * k.CAR_LENGTH * 0.35 + ry * side * k.CAR_WIDTH * 0.4
            pygame.draw.circle(self.skids, (*k.COLOR_SKID, 200),
                               (int(wx + k.VIEW_MARGIN), int(wy + k.VIEW_MARGIN)), 2)

    # -- drawing -----------------------------------------------------------------------

    def draw(self, screen: pygame.Surface, game: Gameplay, show_ghost: bool, show_sensors: bool,
             countdown: float, go_flash: float, popup: tuple[str, float] | None) -> None:
        screen.blit(self.base, self.rect.topleft)
        screen.blit(self.skids, self.rect.topleft)
        if show_ghost and not game.finished:
            frame = game.ghost_frame()
            if frame is not None:
                self._blit_car(screen, self.ghost_sprite, *frame)
        if show_sensors:
            self._draw_sensors(screen, game)
        car = game.car
        self._blit_car(screen, self.car_sprite, car.x, car.y, car.angle)

        if countdown > 0:
            self._draw_center_text(screen, str(math.ceil(countdown)), k.COLOR_TEXT)
        elif go_flash > 0:
            self._draw_center_text(screen, "GO !", k.COLOR_SENSOR_FAR)
        if popup is not None:
            text, age = popup
            label = self.font_popup.render(text, True, k.COLOR_TEXT)
            label.set_alpha(int(255 * min(1.0, (1.6 - age) / 0.4)))
            screen.blit(label, label.get_rect(midtop=(self.rect.centerx, self.rect.y + 40 - int(age * 10))))
        if game.finished:
            self._draw_results(screen, game)

    def _blit_car(self, screen: pygame.Surface, sprite: pygame.Surface, x: float, y: float, angle: float) -> None:
        rotated = pygame.transform.rotozoom(sprite, -math.degrees(angle), 1 / _CAR_SCALE)
        screen.blit(rotated, rotated.get_rect(center=self.to_screen(x, y)))

    def _draw_sensors(self, screen: pygame.Surface, game: Gameplay) -> None:
        start = self.to_screen(game.car.x, game.car.y)
        for s in game.sensors():
            color = _lerp(k.COLOR_SENSOR_NEAR, k.COLOR_SENSOR_FAR, s.distance / k.SENSOR_RANGE)
            end = self.to_screen(s.hit_x, s.hit_y)
            pygame.draw.line(screen, color, start, end, 1)
            pygame.draw.circle(screen, color, end, 3)

    def _draw_center_text(self, screen: pygame.Surface, text: str, color: Color) -> None:
        label = self.font_big.render(text, True, color)
        center = self.rect.center
        backdrop = pygame.Surface((label.get_width() + 60, label.get_height() + 20), pygame.SRCALPHA)
        pygame.draw.rect(backdrop, k.COLOR_SHADE, backdrop.get_rect(), border_radius=24)
        screen.blit(backdrop, backdrop.get_rect(center=center))
        screen.blit(label, label.get_rect(center=center))

    def _draw_results(self, screen: pygame.Surface, game: Gameplay) -> None:
        card = pygame.Rect(0, 0, 360, 280)
        card.center = self.rect.center
        shade = pygame.Surface(card.size, pygame.SRCALPHA)
        pygame.draw.rect(shade, k.COLOR_CARD, shade.get_rect(), border_radius=20)
        screen.blit(shade, card.topleft)
        pygame.draw.rect(screen, k.COLOR_CARD_BORDER, card, width=1, border_radius=20)
        title = self.font_title.render("Arrivée !", True, k.COLOR_TEXT)
        screen.blit(title, title.get_rect(midtop=(card.centerx, card.y + 22)))
        pygame.draw.rect(screen, k.ACCENT, (card.centerx - 30, card.y + 76, 60, 4), border_radius=2)
        best = min(game.lap_times)
        lines = [(f"Temps total   {format_time(game.time)}", k.COLOR_TEXT)]
        for i, t in enumerate(game.lap_times):
            star = "   meilleur" if t == best else ""
            lines.append((f"Tour {i + 1}   {format_time(t)}{star}", k.ACCENT if t == best else k.COLOR_TEXT_SOFT))
        lines.append(("R ou Recommencer pour rejouer", k.COLOR_TEXT_SOFT))
        for i, (text, color) in enumerate(lines):
            label = self.font_body.render(text, True, color)
            screen.blit(label, label.get_rect(midtop=(card.centerx, card.y + 96 + i * 32)))

    # -- pre-rendered sprites ---------------------------------------------------------------

    def _render_track(self) -> pygame.Surface:
        ss = _SUPERSAMPLE
        t = self.track
        w, h = self.rect.size
        big = pygame.Surface((w * ss, h * ss))
        big.fill(k.COLOR_GROUND)
        for gx in range(0, w, 24):   # subtle dot grid on the ground
            for gy in range(0, h, 24):
                pygame.draw.circle(big, k.COLOR_GROUND_DOT, (gx * ss, gy * ss), ss)

        def pts(points):
            return [((x + k.VIEW_MARGIN) * ss, (y + k.VIEW_MARGIN) * ss) for x, y in points]

        left, right = pts(t.left), pts(t.right)
        outer, inner = (left, right) if _area(left) > _area(right) else (right, left)
        pygame.draw.polygon(big, k.COLOR_ASPHALT, outer)
        pygame.draw.polygon(big, k.COLOR_GROUND, inner)
        for gx in range(0, w, 24):   # redraw the dots the inner fill covered
            for gy in range(0, h, 24):
                if _inside(inner, gx * ss, gy * ss):
                    pygame.draw.circle(big, k.COLOR_GROUND_DOT, (gx * ss, gy * ss), ss)

        center = pts(t.center)
        for i in range(0, t.n, 6):   # dashed center line
            pygame.draw.line(big, k.COLOR_CENTER, center[i], center[(i + 3) % t.n], 2 * ss)
        for wall in (left, right):
            pygame.draw.lines(big, k.COLOR_EDGE, True, wall, 2 * ss)
            for i in range(t.n):     # kerbs in the curves only
                if t.curvature(i) > _KERB_CURVE:
                    color = k.COLOR_KERB_A if (i // 2) % 2 else k.COLOR_KERB_B
                    pygame.draw.line(big, color, wall[i], wall[(i + 1) % t.n], 5 * ss)
        self._draw_start_line(big, ss)
        return pygame.transform.smoothscale(big, (w, h))

    def _draw_start_line(self, big: pygame.Surface, ss: int) -> None:
        t = self.track
        (cx, cy), (nx, ny), (tx, ty) = t.center[0], t.normals[0], t.tangents[0]
        size = 6
        cells = int(2 * t.half_width // size)
        for row in range(2):
            for i in range(cells):
                color = (240, 240, 245) if (i + row) % 2 else (20, 20, 26)
                off = -t.half_width + i * size
                x = cx + nx * off + tx * row * size + k.VIEW_MARGIN
                y = cy + ny * off + ty * row * size + k.VIEW_MARGIN
                quad = [(x, y), (x + nx * size, y + ny * size),
                        (x + nx * size + tx * size, y + ny * size + ty * size), (x + tx * size, y + ty * size)]
                pygame.draw.polygon(big, color, [(px * ss, py * ss) for px, py in quad])

    def _render_car(self, body: Color, dark: Color) -> pygame.Surface:
        s = _CAR_SCALE
        L, W = k.CAR_LENGTH * s, k.CAR_WIDTH * s
        surf = pygame.Surface((L + 2 * s, W + 4 * s), pygame.SRCALPHA)
        ox, oy = s, 2 * s
        for wx in (0.12, 0.66):      # wheels stick out a little
            for wy in (-2 * s, W - 2 * s):
                pygame.draw.rect(surf, k.COLOR_WHEEL, (ox + wx * L, oy + wy, 0.22 * L, 4 * s), border_radius=s)
        pygame.draw.rect(surf, dark, (ox, oy, L, W), border_radius=4 * s)
        pygame.draw.rect(surf, body, (ox + s, oy + s, L - 2 * s, W - 2 * s), border_radius=3 * s)
        pygame.draw.rect(surf, k.COLOR_GLASS, (ox + 0.45 * L, oy + 2 * s, 0.25 * L, W - 4 * s), border_radius=2 * s)
        pygame.draw.rect(surf, dark, (ox + 0.12 * L, oy + W / 2 - s, 0.3 * L, 2 * s))  # stripe
        return surf


def _area(points: list[tuple[float, float]]) -> float:
    return abs(sum(x0 * y1 - x1 * y0 for (x0, y0), (x1, y1) in zip(points, points[1:] + points[:1]))) / 2


def _inside(poly: list[tuple[float, float]], x: float, y: float) -> bool:
    inside = False
    for (x0, y0), (x1, y1) in zip(poly, poly[1:] + poly[:1]):
        if (y0 > y) != (y1 > y) and x < x0 + (y - y0) * (x1 - x0) / (y1 - y0):
            inside = not inside
    return inside
