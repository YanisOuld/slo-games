"""Connect Four layout, animation tuning and palette (view choices only)."""
from engine import constants as screen
from engine import sidebar, theme

NAV_WIDTH = sidebar.WIDTH
BOARD_X = NAV_WIDTH
BOARD_WIDTH = screen.SCREEN_WIDTH - NAV_WIDTH

MARGIN = 26       # around board + preview row
BOARD_PAD = 12    # board edge around the holes
DISC_RATIO = 0.40  # disc radius / cell size

GRAVITY = 4200    # px/s², falling discs
BOUNCE = 0.28     # fraction of speed kept on the bounce
AI_MIN_THINK = 0.35  # seconds: even a fast AI "thinks" a little, so you see its turn

ACCENT = theme.PURPLE
COLOR_RED = theme.RED
COLOR_YELLOW = theme.YELLOW
COLOR_BOARD = sidebar.mix(theme.SURFACE_RAISED, theme.PURPLE, 0.28)
COLOR_HOLE_RIM = sidebar.mix(theme.SURFACE, theme.PURPLE, 0.18)
COLOR_BEHIND = theme.BG                    # seen through empty holes
COLOR_COLUMN = theme.SURFACE_HOVER         # hovered column, behind the board
COLOR_SHADOW = (6, 6, 10)
COLOR_WIN = theme.TEXT
