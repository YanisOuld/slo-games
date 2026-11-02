"""Battleship layout, timing and palette (view choices only).

Touch-first: everything is a tap or a drag with one finger (no right click, no
keyboard), and nothing heavy is computed per frame, so it runs on a Raspberry Pi.
"""
from engine import sidebar, theme

NAV_WIDTH = sidebar.WIDTH

# Big grid: the one you shoot at (or place your fleet on).
BIG_X, BIG_Y, BIG_CELL = NAV_WIDTH + 52, 84, 40
# Right column: your fleet in small during battle, the ship dock during placement.
SIDE_X, SIDE_W = NAV_WIDTH + 470, 206
MINI_Y, MINI_CELL = 84, 20
DOCK_Y, DOCK_CELL, DOCK_GAP = 84, 28, 18
DRAG_THRESHOLD = 8      # px a press must move to count as a drag (else it's a tap)

AI_DELAY = 0.75         # seconds the AI "aims" before firing
EFFECT_TIME = 0.6       # splash / explosion animation length

ACCENT = theme.ORANGE
COLOR_WATER_TOP = (18, 40, 70)
COLOR_WATER_BOTTOM = (12, 28, 52)
COLOR_WAVE = (28, 58, 96)
COLOR_GRID = (38, 70, 108)
COLOR_LABEL = theme.TEXT_DIM
COLOR_TITLE = theme.TEXT
COLOR_SHIP = (150, 162, 184)
COLOR_SHIP_DARK = (96, 106, 126)
COLOR_SHIP_SUNK = (92, 58, 66)
COLOR_SUNK_EDGE = theme.RED
COLOR_MISS = (150, 185, 225)
COLOR_HIT = theme.ORANGE
COLOR_FIRE = theme.YELLOW
COLOR_VALID = theme.GREEN
COLOR_INVALID = theme.RED
COLOR_HOVER = theme.ORANGE
COLOR_HEAT_COLD = (40, 90, 200)
COLOR_HEAT_HOT = (255, 90, 40)
COLOR_TEXT = theme.TEXT
COLOR_TEXT_SOFT = theme.TEXT_SOFT
COLOR_TEXT_DIM = theme.TEXT_DIM
COLOR_CARD = (*theme.SURFACE, 235)
COLOR_CARD_BORDER = theme.BORDER
