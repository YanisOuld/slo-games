"""Runner views. They draw only; they never mutate the model (input lives in the Scene)."""
from __future__ import annotations

import math
from typing import Callable

import pygame

from engine import constants as sc
from engine.widget import Button, Widget

from . import constants as k
from .game import Gameplay
from .models import ObstacleKind, Statistics


def _hill_layer(color: tuple[int, int, int], base: int, amplitude: int, waves: tuple[int, ...]) -> pygame.Surface:
    """A screen-wide hill silhouette that tiles seamlessly (integer number of waves)."""
    w, h = sc.SCREEN_WIDTH, sc.SCREEN_HEIGHT
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    points = [(0, h)]
    for x in range(0, w + 1, 8):
        y = base - sum(amplitude / (i + 1) * math.sin(2 * math.pi * n * x / w + i)
                       for i, n in enumerate(waves))
        points.append((x, y))
    points.append((w, h))
    pygame.draw.polygon(surf, color, points)
    return surf


def _sky(top: tuple[int, int, int], bottom: tuple[int, int, int]) -> pygame.Surface:
    surf = pygame.Surface((sc.SCREEN_WIDTH, sc.SCREEN_HEIGHT))
    for y in range(sc.SCREEN_HEIGHT):
        t = y / sc.SCREEN_HEIGHT
        color = [int(a + (b - a) * t) for a, b in zip(top, bottom)]
        pygame.draw.line(surf, color, (0, y), (sc.SCREEN_WIDTH, y))
    return surf


_SKY_FADE = 1.5  # seconds to blend into a new zone's sky


class WorldView(Widget):
    """Draws the scrolling world: sky, parallax hills, ground, obstacles, coins, player."""

    def __init__(self) -> None:
        super().__init__(0, 0, sc.SCREEN_WIDTH, sc.SCREEN_HEIGHT)
        self.skies = [_sky(top, bottom) for top, bottom in k.ZONE_SKIES]
        # (surface, parallax factor): farther layers scroll slower.
        self.layers = [
            (_hill_layer(k.HILLS_FAR, 330, 70, (2, 5, 9)), 0.15),
            (_hill_layer(k.HILLS_NEAR, 400, 50, (3, 7, 11)), 0.35),
        ]

    def draw(self, screen: pygame.Surface, game: Gameplay, zone_age: float) -> None:
        """zone_age: seconds since the current zone started (drives the sky fade)."""
        cam = game.camera_x
        self._draw_sky(screen, game.zone, zone_age)
        for surf, factor in self.layers:
            off = -(cam * factor) % sc.SCREEN_WIDTH
            screen.blit(surf, (off - sc.SCREEN_WIDTH, 0))
            screen.blit(surf, (off, 0))

        for g in game.ground:
            self._draw_ground(screen, g.x0 - cam, g.x1 - cam)
        for s in game.platforms:
            rect = pygame.Rect(s.x0 - cam, s.y, s.x1 - s.x0, k.PLATFORM_THICKNESS)
            pygame.draw.rect(screen, k.PLATFORM, rect, border_radius=5)
            pygame.draw.rect(screen, k.PLATFORM_TOP, (rect.x, rect.y, rect.w, 5), border_radius=3)
        for coin in game.coin_list:
            self._draw_coin(screen, coin.x - cam, coin.y, game.time)
        for ob in game.obstacles:
            rect = pygame.Rect(ob.box.x - cam, ob.box.y, ob.box.w, ob.box.h)
            if ob.kind is ObstacleKind.BLOCK:
                self._draw_block(screen, rect)
            elif ob.kind is ObstacleKind.DRONE:
                rect.y += int(3 * math.sin(game.time * 8))  # hover bob (cosmetic only)
                self._draw_drone(screen, rect, game.time, k.DRONE)
            elif ob.kind is ObstacleKind.WAVE_DRONE:
                self._draw_drone(screen, rect, game.time, k.WAVE_DRONE)
            elif ob.kind is ObstacleKind.SLIME:
                self._draw_slime(screen, rect, game.time, ob.stomped)
            elif ob.kind is ObstacleKind.CEILING:
                self._draw_ceiling(screen, rect)
            elif ob.kind is ObstacleKind.MISSILE:
                self._draw_missile(screen, rect, game.time)
        for warning in game.warnings:
            self._draw_warning(screen, warning.bottom - k.MISSILE_H / 2, warning.time_left)
        self._draw_player(screen, game, cam)

    # -- drawing helpers -------------------------------------------------------------

    def _draw_sky(self, screen: pygame.Surface, zone: int, zone_age: float) -> None:
        current = self.skies[(zone - 1) % len(self.skies)]
        if zone > 1 and zone_age < _SKY_FADE:
            screen.blit(self.skies[(zone - 2) % len(self.skies)], (0, 0))
            current.set_alpha(int(255 * zone_age / _SKY_FADE))
            screen.blit(current, (0, 0))
            current.set_alpha(None)
        else:
            screen.blit(current, (0, 0))

    def _draw_ground(self, screen: pygame.Surface, x0: float, x1: float) -> None:
        rect = pygame.Rect(x0, k.GROUND_Y, x1 - x0, sc.SCREEN_HEIGHT - k.GROUND_Y)
        pygame.draw.rect(screen, k.GROUND_DIRT, rect)
        for y in range(k.GROUND_Y + 30, sc.SCREEN_HEIGHT, 30):  # soil strata
            pygame.draw.line(screen, k.GROUND_DIRT_DARK, (rect.x, y), (rect.right - 1, y), 3)
        pygame.draw.rect(screen, k.GROUND_TOP, (rect.x, rect.y, rect.w, 10))

    def _draw_block(self, screen: pygame.Surface, rect: pygame.Rect) -> None:
        pygame.draw.rect(screen, k.BLOCK_DARK, rect, border_radius=4)
        pygame.draw.rect(screen, k.BLOCK, rect.inflate(-6, -6), border_radius=3)
        pygame.draw.line(screen, k.BLOCK_DARK, rect.inflate(-10, -10).topleft,
                         rect.inflate(-10, -10).bottomright, 3)

    def _draw_drone(self, screen: pygame.Surface, rect: pygame.Rect, t: float,
                    color: tuple[int, int, int]) -> None:
        pygame.draw.rect(screen, color, rect, border_radius=8)
        pygame.draw.circle(screen, k.DRONE_LIGHT, rect.center, 4)
        spin = abs(math.sin(t * 40)) * 14 + 4  # propellers blur by changing width
        for px in (rect.x + 8, rect.right - 8):
            pygame.draw.line(screen, color, (px, rect.y), (px, rect.y - 6), 2)
            pygame.draw.line(screen, k.HUD_DIM, (px - spin / 2, rect.y - 6), (px + spin / 2, rect.y - 6), 2)

    def _draw_slime(self, screen: pygame.Surface, rect: pygame.Rect, t: float, stomped: bool) -> None:
        if stomped:
            flat = pygame.Rect(rect.x - 6, rect.bottom - 8, rect.w + 12, 8)
            pygame.draw.ellipse(screen, k.SLIME_DARK, flat)
            return
        squish = int(3 * math.sin(t * 10))  # wobbles as it crawls
        body = pygame.Rect(rect.x - squish, rect.y + squish, rect.w + 2 * squish, rect.h - squish + 6)
        pygame.draw.ellipse(screen, k.SLIME_DARK, body)
        pygame.draw.ellipse(screen, k.SLIME, body.inflate(-6, -6))
        pygame.draw.rect(screen, k.SLIME_DARK, (body.x, rect.bottom, body.w, 6))  # flat base
        for ex in (body.x + body.w // 3, body.x + 2 * body.w // 3 - 6):  # eyes look left
            pygame.draw.circle(screen, (250, 250, 250), (ex, body.y + 10), 5)
            pygame.draw.circle(screen, k.PLAYER_EYE, (ex - 2, body.y + 10), 2)

    def _draw_ceiling(self, screen: pygame.Surface, rect: pygame.Rect) -> None:
        spike_h, spike_w = 16, 18
        slab = pygame.Rect(rect.x, rect.y, rect.w, rect.h - spike_h)
        pygame.draw.rect(screen, k.CEILING, slab)
        for sx in range(rect.x, rect.right - spike_w + 1, spike_w):
            pygame.draw.polygon(screen, k.SPIKE, [
                (sx, slab.bottom), (sx + spike_w, slab.bottom), (sx + spike_w // 2, rect.bottom)])

    def _draw_missile(self, screen: pygame.Surface, rect: pygame.Rect, t: float) -> None:
        body = rect.inflate(-10, 0).move(5, 0)
        pygame.draw.rect(screen, k.MISSILE, body, border_radius=4)
        pygame.draw.polygon(screen, k.MISSILE_NOSE, [  # nose points left, toward the player
            (rect.x, rect.centery), (body.x + 2, rect.y), (body.x + 2, rect.bottom)])
        flame = 10 + int(6 * abs(math.sin(t * 30)))
        pygame.draw.polygon(screen, k.FLAME, [
            (body.right, rect.y + 3), (body.right, rect.bottom - 3), (body.right + flame, rect.centery)])

    def _draw_warning(self, screen: pygame.Surface, y: float, time_left: float) -> None:
        # Blinks faster as launch approaches.
        if math.sin(time_left * (10 + 20 * (1 - time_left))) < -0.3:
            return
        center = (sc.SCREEN_WIDTH - 36, int(y))
        pygame.draw.circle(screen, k.WARNING, center, 18)
        pygame.draw.rect(screen, (255, 255, 255), (center[0] - 2, center[1] - 11, 5, 14))
        pygame.draw.rect(screen, (255, 255, 255), (center[0] - 2, center[1] + 6, 5, 5))

    def _draw_coin(self, screen: pygame.Surface, x: float, y: float, t: float) -> None:
        r = k.COIN_RADIUS
        width = max(2, int(2 * r * abs(math.cos(t * 4 + x * 0.01))))  # spinning
        rect = pygame.Rect(0, 0, width, 2 * r)
        rect.center = (int(x), int(y))
        pygame.draw.ellipse(screen, k.COIN, rect)
        if width > 6:
            pygame.draw.ellipse(screen, k.COIN_SHINE, rect.inflate(-width // 2, -r))

    def _draw_player(self, screen: pygame.Surface, game: Gameplay, cam: float) -> None:
        p = game.player
        box = p.box
        body = pygame.Rect(box.x - cam, box.y, box.w, box.h - 8)
        # Legs: alternate while running, tucked in the air.
        if p.on_ground:
            phase = math.sin(game.distance / 18)
            for i, side in enumerate((-1, 1)):
                lift = int(4 * max(0.0, phase * side))
                pygame.draw.rect(screen, k.PLAYER_DARK,
                                 (body.x + 5 + i * 15, body.bottom - lift, 9, 8 - lift + 2))
        else:
            pygame.draw.rect(screen, k.PLAYER_DARK, (body.x + 6, body.bottom, body.w - 12, 6))
        pygame.draw.rect(screen, k.PLAYER, body, border_radius=8)
        pygame.draw.rect(screen, k.PLAYER_DARK, (body.x, body.y + body.h // 2, body.w, 4))
        eye_y = body.y + (8 if p.ducking else 12)
        pygame.draw.circle(screen, (250, 250, 250), (body.right - 9, eye_y), 6)
        pygame.draw.circle(screen, k.PLAYER_EYE, (body.right - 7, eye_y), 3)


_BANNER_TIME = 2.5  # seconds the zone banner stays up


class HudPanel(Widget):
    def __init__(self) -> None:
        super().__init__(0, 0, sc.SCREEN_WIDTH, 60)
        self.font_big = pygame.font.SysFont(None, 48)
        self.font_small = pygame.font.SysFont(None, 28)
        self.font_banner = pygame.font.SysFont(None, 72)

    def draw(self, screen: pygame.Surface, stats: Statistics, zone_age: float) -> None:
        screen.blit(self.font_big.render(f"{stats.score}", True, k.HUD_TEXT), (24, 18))
        info = (f"{stats.meters} m   ·   {stats.coins} pièces   ·   {stats.stomps} slimes"
                f"   ·   {stats.speed / k.PX_PER_METER:.0f} m/s")
        screen.blit(self.font_small.render(info, True, k.HUD_DIM), (24, 58))
        for i, text in enumerate((f"Record : {stats.best}", f"Zone {stats.zone}")):
            label = self.font_small.render(text, True, k.HUD_DIM)
            screen.blit(label, label.get_rect(topright=(sc.SCREEN_WIDTH - 24, 24 + i * 28)))
        if stats.zone > 1 and zone_age < _BANNER_TIME:
            self._draw_banner(screen, stats.zone, zone_age)

    def _draw_banner(self, screen: pygame.Surface, zone: int, age: float) -> None:
        # Fade in quickly, hold, fade out.
        alpha = int(255 * min(1.0, age / 0.3, (_BANNER_TIME - age) / 0.6))
        news = k.ZONE_NEWS.get(zone, "Plus vite !")
        cx = sc.SCREEN_WIDTH // 2
        for text, font, y in ((f"Zone {zone}", self.font_banner, 150), (news, self.font_small, 200)):
            label = font.render(text, True, k.HUD_TEXT)
            label.set_alpha(alpha)
            screen.blit(label, label.get_rect(center=(cx, y)))


class OverlayPanel(Widget):
    """Darkened screen with a title, a few lines of text and buttons (pause, game over, start)."""

    def __init__(self, title: str, actions: tuple[tuple[str, Callable[[], None]], ...]) -> None:
        super().__init__(0, 0, sc.SCREEN_WIDTH, sc.SCREEN_HEIGHT)
        self.title = title
        self.lines: list[str] = []
        self.font_title = pygame.font.SysFont(None, 80)
        self.font_body = pygame.font.SysFont(None, 32)
        self.shade = pygame.Surface((sc.SCREEN_WIDTH, sc.SCREEN_HEIGHT), pygame.SRCALPHA)
        self.shade.fill(k.OVERLAY_SHADE)

        bw, bh, gap = 300, 52, 14
        bx = (sc.SCREEN_WIDTH - bw) // 2
        top = 300
        self.buttons = [
            Button(bx, top + i * (bh + gap), bw, bh, label, self.font_body, cb)
            for i, (label, cb) in enumerate(actions)
        ]

    def handle_event(self, event: pygame.event.Event) -> None:
        for b in self.buttons:
            b.handle_event(event)

    def draw(self, screen: pygame.Surface) -> None:
        screen.blit(self.shade, (0, 0))
        cx = sc.SCREEN_WIDTH // 2
        title = self.font_title.render(self.title, True, k.HUD_TEXT)
        screen.blit(title, title.get_rect(center=(cx, 150)))
        for i, line in enumerate(self.lines):
            text = self.font_body.render(line, True, k.HUD_DIM)
            screen.blit(text, text.get_rect(center=(cx, 210 + i * 34)))
        for b in self.buttons:
            b.draw(screen)
