"""Minesweeper layout and palette (view choices only)."""
from engine import constants as screen
from engine import sidebar, theme

NAV_WIDTH = sidebar.WIDTH
BOARD_X = NAV_WIDTH
BOARD_WIDTH = screen.SCREEN_WIDTH - NAV_WIDTH

PADDING = 20

# When the AI is playing, it makes one move every AI_INTERVAL seconds.
AI_INTERVAL = 0.12

COLOR_BOARD_BG = theme.SURFACE
COLOR_HIDDEN = (72, 78, 104)
COLOR_HIDDEN_HOVER = (94, 101, 132)
COLOR_REVEALED = theme.SURFACE_RAISED
COLOR_EXPLODED = theme.RED
COLOR_MINE = theme.BG
COLOR_FLAG = theme.RED
COLOR_FLAG_POLE = theme.LIGHT
COLOR_WRONG_FLAG = theme.YELLOW
COLOR_HINT_SAFE = theme.GREEN
COLOR_HINT_MINE = theme.RED
COLOR_HINT_GUESS = theme.YELLOW
CELL_GAP = 1
CELL_RADIUS = 3

NUMBER_COLORS = {
    1: (100, 160, 255),
    2: (100, 210, 120),
    3: (240, 100, 100),
    4: (180, 120, 245),
    5: (245, 170, 70),
    6: (80, 215, 215),
    7: (235, 235, 235),
    8: (160, 160, 160),
}

ACCENT = theme.RED
