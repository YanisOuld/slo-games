"""Binairo layout and palette (view choices only)."""
from engine import constants as screen

GRID_SIZE = 20  # must stay even

NAV_WIDTH = 400
BOARD_X = NAV_WIDTH
BOARD_WIDTH = screen.SCREEN_WIDTH - NAV_WIDTH

PADDING = 20
STAT_MARGIN = 44  # room reserved for the counters around the board

COLOR_EMPTY = (236, 233, 227)
COLOR_WHITE = (244, 200, 206)
COLOR_BLACK = (120, 18, 28)
COLOR_HINT = (200, 40, 40)
COLOR_STAT = (225, 225, 225)
CELL_GAP = 2
CELL_RADIUS = 6

NAV_BG = (10, 10, 10)
NAV_TITLE = (240, 240, 240)
NAV_TEXT = (200, 200, 200)
NAV_LOGO = (235, 235, 235)
