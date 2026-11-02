"""Binairo layout and palette (view choices only)."""
from engine import constants as screen
from engine import sidebar, theme

GRID_SIZE = 20  # must stay even

NAV_WIDTH = sidebar.WIDTH
BOARD_X = NAV_WIDTH
BOARD_WIDTH = screen.SCREEN_WIDTH - NAV_WIDTH

PADDING = 28         # around the board frame
FRAME_PAD = 10       # inside the frame, around the cells
COUNTER_MARGIN = 42  # room for the per-row / per-column counters
CELL_GAP = 2
BEVEL = 3            # darker bottom edge that makes placed tiles look raised

# Board
COLOR_FRAME = theme.SURFACE
COLOR_FRAME_BORDER = theme.BORDER
COLOR_EMPTY = theme.SURFACE_RAISED
COLOR_EMPTY_FOCUS = theme.SURFACE_HOVER   # empty cells in the hovered row/column
COLOR_WHITE = theme.LIGHT
COLOR_BLACK = theme.BLUE
COLOR_HOVER = theme.TEXT
COLOR_HINT = theme.TEXT_SOFT
COLOR_HINT_BG = theme.BG
COLOR_ERROR = theme.RED
COLOR_DONE = theme.GREEN
COLOR_STAT = theme.TEXT_DIM
COLOR_SHADE = (*theme.BG, 200)

COLOR_TEXT = theme.TEXT
COLOR_TEXT_SOFT = theme.TEXT_SOFT
ACCENT = theme.BLUE
