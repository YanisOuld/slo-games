"""Minesweeper layout and palette (view choices only)."""
from engine import constants as screen

NAV_WIDTH = 400
BOARD_X = NAV_WIDTH
BOARD_WIDTH = screen.SCREEN_WIDTH - NAV_WIDTH

PADDING = 20

# When the AI is playing, it makes one move every AI_INTERVAL seconds.
AI_INTERVAL = 0.12

COLOR_BOARD_BG = (24, 24, 30)
COLOR_HIDDEN = (70, 78, 98)
COLOR_HIDDEN_HOVER = (92, 102, 128)
COLOR_REVEALED = (36, 38, 46)
COLOR_EXPLODED = (200, 60, 60)
COLOR_MINE = (15, 15, 15)
COLOR_FLAG = (235, 80, 80)
COLOR_FLAG_POLE = (230, 230, 230)
COLOR_WRONG_FLAG = (255, 210, 60)
COLOR_HINT_SAFE = (110, 230, 130)
COLOR_HINT_MINE = (240, 80, 80)
COLOR_HINT_GUESS = (240, 190, 70)
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

NAV_BG = (10, 10, 10)
NAV_TITLE = (240, 240, 240)
NAV_TEXT = (200, 200, 200)
NAV_HELP = (140, 140, 140)
NAV_LOGO = (235, 235, 235)
