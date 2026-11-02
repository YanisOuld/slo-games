"""Billiards views. They draw only; they never mutate the model (input lives in the Scene).

Cheap per frame (Raspberry Pi): the table and the 16 ball sprites are rendered once;
a frame is a table blit, 16 ball blits, and a few lines for the cue and the guide.
"""
from __future__ import annotations

import math

import pygame

from . import constants as k
from . import physics
from .game import Gameplay
from .models import Group, Phase
from .physics import POCKETS, R

Color = tuple[int, int, int]
_SUPERSAMPLE = 4


def to_screen(x: float, y: float) -> tuple[int, int]:
    return int(k.PLAY_X + x), int(k.PLAY_Y + y)


def to_table(px: int, py: int) -> tuple[float, float]:
    return float(px - k.PLAY_X), float(py - k.PLAY_Y)


def _lerp(a: Color, b: Color, t: float) -> Color:
    return tuple(int(x + (y - x) * t) for x, y in zip(a, b))


def power_color(p: float) -> Color:
    return _lerp(k.POWER_LOW, k.POWER_MID, p * 2) if p < 0.5 else _lerp(k.POWER_MID, k.POWER_HIGH, p * 2 - 1)


class TableView:
    def __init__(self) -> None:
        self.table_surface = self._render_table()
        self.sprites = {n: self._render_ball(n, R) for n in range(16)}
        self.small = {n: self._render_ball(n, 7) for n in range(16)}   # for the player cards
        self.font_card = pygame.font.SysFont(None, 60)
        self.font_body = pygame.font.SysFont(None, 27)
        self.font_label = pygame.font.SysFont(None, 22)
        self.font_name = pygame.font.SysFont(None, 30)

    # -- table -----------------------------------------------------------------------

    def draw_table(self, screen: pygame.Surface, game: Gameplay, sinking: list[tuple[int, tuple[float, float], float]]) -> None:
        screen.blit(self.table_surface, (k.TABLE_X, k.TABLE_Y))
        for ball in game.table.balls:
            if ball.pocketed:
                continue
            sx, sy = to_screen(ball.x, ball.y)
            pygame.draw.circle(screen, k.COLOR_SHADOW, (sx + 2, sy + 3), int(R))
            sprite = self.sprites[ball.number]
            screen.blit(sprite, sprite.get_rect(center=(sx, sy)))
        for number, (px, py), age in sinking:   # potted balls shrink into the pocket
            scale = max(0.05, 1 - age / k.POT_ANIM)
            sprite = pygame.transform.smoothscale(self.sprites[number],
                                                  (max(1, int(2 * R * scale)),) * 2)
            screen.blit(sprite, sprite.get_rect(center=to_screen(px, py)))

    def draw_aim(self, screen: pygame.Surface, game: Gameplay, angle: float, power: float, guide: bool) -> None:
        cue = game.table.cue
        cx, cy = to_screen(cue.x, cue.y)
        dx, dy = math.cos(angle), math.sin(angle)
        if guide:
            (gx, gy), hit = game.table.predict(angle)
            gsx, gsy = to_screen(gx, gy)
            _dashed(screen, k.COLOR_AIM, (cx, cy), (gsx, gsy))
            pygame.draw.circle(screen, k.COLOR_GHOST, (gsx, gsy), int(R), 1)
            if hit is not None:   # where the object ball will go
                nx, ny = hit.x - gx, hit.y - gy
                n = math.hypot(nx, ny) or 1
                hx, hy = to_screen(hit.x, hit.y)
                pygame.draw.line(screen, k.COLOR_AIM, (hx, hy), (hx + nx / n * 50, hy + ny / n * 50), 2)
        else:
            pygame.draw.line(screen, k.COLOR_AIM, (cx, cy), (cx + dx * 60, cy + dy * 60), 1)
        self._draw_cue(screen, (cx, cy), dx, dy, power)

    def _draw_cue(self, screen: pygame.Surface, center: tuple[int, int], dx: float, dy: float, power: float) -> None:
        """The stick lies behind the cue ball, pulled back with the power."""
        gap = R + k.CUE_GAP + k.CUE_PULL * power
        tip = (center[0] - dx * gap, center[1] - dy * gap)
        px, py = -dy, dx   # perpendicular
        sections = ((0, 6, 2.0, k.COLOR_CUE_TIP), (6, 16, 2.2, k.COLOR_CUE_FERRULE),
                    (16, 170, 2.4, k.COLOR_CUE_SHAFT), (170, k.CUE_LENGTH, 3.6, k.COLOR_CUE_BUTT))
        for start, end, half, color in sections:
            w0, w1 = half + start / k.CUE_LENGTH * 2.2, half + end / k.CUE_LENGTH * 2.2  # tapers
            a = (tip[0] - dx * start, tip[1] - dy * start)
            b = (tip[0] - dx * end, tip[1] - dy * end)
            pygame.draw.polygon(screen, color, [(a[0] + px * w0, a[1] + py * w0), (b[0] + px * w1, b[1] + py * w1),
                                                (b[0] - px * w1, b[1] - py * w1), (a[0] - px * w0, a[1] - py * w0)])

    def draw_power_bar(self, screen: pygame.Surface, power: float, active: bool) -> None:
        track = pygame.Rect(k.BAR_X, k.PLAY_Y, k.BAR_W, int(physics.H))
        pygame.draw.rect(screen, k.COLOR_PANEL, track, border_radius=k.BAR_W // 2)
        if power > 0:
            fill = pygame.Rect(track.x + 4, track.y + 4, track.w - 8, int((track.h - 8) * power))
            pygame.draw.rect(screen, power_color(power), fill, border_radius=(track.w - 8) // 2)
        handle_y = track.y + 4 + int((track.h - 8) * power)
        pygame.draw.rect(screen, k.COLOR_TEXT if active else k.COLOR_TEXT_DIM,
                         (track.x - 4, handle_y - 4, track.w + 8, 8), border_radius=4)
        for i, letter in enumerate("TIRER"):   # vertical hint below the gauge
            label = self.font_label.render(letter, True, k.COLOR_TEXT_DIM)
            screen.blit(label, label.get_rect(center=(track.centerx, track.bottom + 16 + i * 16)))

    # -- header and overlays ---------------------------------------------------------------

    def draw_players(self, screen: pygame.Surface, game: Gameplay, ball_in_hand: bool) -> None:
        w = (k.TABLE_W - 16) // 2
        for i, player in enumerate(game.players):
            card = pygame.Rect(k.TABLE_X + i * (w + 16), k.HEADER_Y, w, 76)
            active = i == game.current and game.phase is not Phase.OVER
            pygame.draw.rect(screen, k.COLOR_PANEL_ACTIVE if active else k.COLOR_PANEL, card, border_radius=12)
            if active:
                pygame.draw.rect(screen, k.ACCENT, card, 2, border_radius=12)
            screen.blit(self.font_name.render(player.name, True, k.COLOR_TEXT), (card.x + 14, card.y + 10))
            tag = player.group.value if player.group else "Table ouverte"
            if active and ball_in_hand:
                tag += "  ·  bille en main"
            screen.blit(self.font_label.render(tag, True, k.COLOR_TEXT_DIM), (card.x + 14, card.y + 38))
            if player.group is not None:   # the balls this player still has to pot
                left = game.remaining(player.group) or [8]
                for j, number in enumerate(left):
                    sprite = self.small[number]
                    screen.blit(sprite, sprite.get_rect(center=(card.x + 22 + j * 18, card.y + 62)))

    def draw_result(self, screen: pygame.Surface, title: str, lines: list[str]) -> None:
        card = pygame.Rect(0, 0, 360, 92 + 32 * len(lines))
        card.center = (k.TABLE_X + k.TABLE_W // 2, k.TABLE_Y + k.TABLE_H // 2)
        shade = pygame.Surface(card.size, pygame.SRCALPHA)
        pygame.draw.rect(shade, k.COLOR_CARD, shade.get_rect(), border_radius=20)
        screen.blit(shade, card.topleft)
        pygame.draw.rect(screen, k.COLOR_BORDER, card, 1, border_radius=20)
        label = self.font_card.render(title, True, k.COLOR_TEXT)
        screen.blit(label, label.get_rect(midtop=(card.centerx, card.y + 20)))
        pygame.draw.rect(screen, k.ACCENT, (card.centerx - 30, card.y + 72, 60, 4), border_radius=2)
        for i, line in enumerate(lines):
            text = self.font_body.render(line, True, k.COLOR_TEXT_SOFT)
            screen.blit(text, text.get_rect(midtop=(card.centerx, card.y + 90 + i * 32)))

    # -- pre-rendered surfaces -------------------------------------------------------------

    def _render_table(self) -> pygame.Surface:
        ss = _SUPERSAMPLE
        w, h = k.TABLE_W, k.TABLE_H
        big = pygame.Surface((w * ss, h * ss), pygame.SRCALPHA)
        pygame.draw.rect(big, k.COLOR_RAIL_EDGE, big.get_rect(), border_radius=18 * ss)
        pygame.draw.rect(big, k.COLOR_RAIL, big.get_rect().inflate(-6 * ss, -6 * ss), border_radius=15 * ss)
        cloth = pygame.Rect((k.RAIL - 6) * ss, (k.RAIL - 6) * ss, (w - 2 * k.RAIL + 12) * ss, (h - 2 * k.RAIL + 12) * ss)
        pygame.draw.rect(big, k.COLOR_CUSHION, cloth, border_radius=4 * ss)
        pygame.draw.rect(big, k.COLOR_CLOTH, (k.RAIL * ss, k.RAIL * ss, int(physics.W) * ss, int(physics.H) * ss))
        hx = k.RAIL + physics.HEAD_SPOT[0]   # head string and spots, faint
        pygame.draw.line(big, k.COLOR_CLOTH_DARK, (hx * ss, k.RAIL * ss), (hx * ss, (h - k.RAIL) * ss), ss)
        for sx, sy in (physics.HEAD_SPOT, physics.FOOT_SPOT):
            pygame.draw.circle(big, k.COLOR_CLOTH_DARK, ((k.RAIL + sx) * ss, (k.RAIL + sy) * ss), 2 * ss)
        for i in range(1, 8):                # diamonds on the rails
            if i == 4:
                continue
            x = k.RAIL + physics.W * i / 8
            for y in (k.RAIL / 2 - 1, h - k.RAIL / 2 + 1):
                pygame.draw.circle(big, k.COLOR_DIAMOND, (x * ss, y * ss), 2 * ss)
        for i in (1, 2, 3):
            y = k.RAIL + physics.H * i / 4
            for x in (k.RAIL / 2 - 1, w - k.RAIL / 2 + 1):
                pygame.draw.circle(big, k.COLOR_DIAMOND, (x * ss, y * ss), 2 * ss)
        for px, py in POCKETS:
            center = ((k.RAIL + px) * ss, (k.RAIL + py) * ss)
            pygame.draw.circle(big, k.COLOR_RAIL_EDGE, center, (k.POCKET_RADIUS + 3) * ss)
            pygame.draw.circle(big, k.COLOR_POCKET, center, k.POCKET_RADIUS * ss)
        return pygame.transform.smoothscale(big, (w, h))

    def _render_ball(self, number: int, radius: float) -> pygame.Surface:
        ss = _SUPERSAMPLE
        r = int(radius * ss)
        big = pygame.Surface((2 * r, 2 * r), pygame.SRCALPHA)
        c = (r, r)
        white = (240, 238, 230)
        if number == 0:
            pygame.draw.circle(big, white, c, r)
        elif Group.of(number) is Group.STRIPES:
            pygame.draw.circle(big, white, c, r)
            band = pygame.Surface((2 * r, 2 * r), pygame.SRCALPHA)
            pygame.draw.rect(band, k.BALL_COLORS[number - 8], (0, int(r * 0.45), 2 * r, int(r * 1.1)))
            mask = pygame.Surface((2 * r, 2 * r), pygame.SRCALPHA)
            pygame.draw.circle(mask, (255, 255, 255, 255), c, r)
            band.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)   # keep the band inside the ball
            big.blit(band, (0, 0))
        else:
            pygame.draw.circle(big, k.BALL_COLORS[number], c, r)
        if number:
            pygame.draw.circle(big, white, c, int(r * 0.42))
            font = pygame.font.SysFont(None, max(8, int(r * 0.75)), bold=True)
            label = font.render(str(number), True, (20, 20, 24))
            big.blit(label, label.get_rect(center=c))
        pygame.draw.circle(big, (255, 255, 255), (int(r * 0.62), int(r * 0.55)), max(1, int(r * 0.16)))  # shine
        return pygame.transform.smoothscale(big, (int(2 * radius), int(2 * radius)))


def _dashed(screen: pygame.Surface, color: Color, a: tuple[int, int], b: tuple[int, int], dash: int = 8) -> None:
    length = math.dist(a, b)
    if length < 1:
        return
    dx, dy = (b[0] - a[0]) / length, (b[1] - a[1]) / length
    for start in range(0, int(length), dash * 2):
        end = min(length, start + dash)
        pygame.draw.line(screen, color, (a[0] + dx * start, a[1] + dy * start), (a[0] + dx * end, a[1] + dy * end), 2)
