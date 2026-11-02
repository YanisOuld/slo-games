"""Snake layout and palette (view choices only)."""
from engine import constants as screen
from engine import sidebar, theme

GRID_COLS = 24
GRID_ROWS = 20

NAV_WIDTH = sidebar.WIDTH
BOARD_X = NAV_WIDTH
BOARD_WIDTH = screen.SCREEN_WIDTH - NAV_WIDTH

PADDING = 20

# Movement speed: the snake steps once every MOVE_INTERVAL seconds, shrinking
# toward MIN_INTERVAL as the score grows (each point removes a little time).
MOVE_INTERVAL = 0.14
MIN_INTERVAL = 0.06
SPEEDUP_PER_POINT = 0.004

# When the AI is driving, how long it lingers on the game-over screen before it
# "presses" Nouvelle partie and plays again.
COLOR_GRID_BG = theme.SURFACE
COLOR_GRID_LINE = (28, 30, 44)
COLOR_SNAKE_HEAD = (180, 245, 180)
COLOR_SNAKE_BODY = theme.GREEN
COLOR_FOOD = theme.RED
CELL_GAP = 1
CELL_RADIUS = 4

ACCENT = theme.GREEN
