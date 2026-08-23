"""Snake layout and palette (view choices only)."""
from engine import constants as screen

GRID_COLS = 24
GRID_ROWS = 20

NAV_WIDTH = 400
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
AI_RESTART_DELAY = 1.2

COLOR_GRID_BG = (24, 28, 24)
COLOR_GRID_LINE = (34, 40, 34)
COLOR_SNAKE_HEAD = (120, 220, 120)
COLOR_SNAKE_BODY = (70, 170, 90)
COLOR_FOOD = (220, 70, 80)
CELL_GAP = 1
CELL_RADIUS = 4

NAV_BG = (10, 10, 10)
NAV_TITLE = (240, 240, 240)
NAV_TEXT = (200, 200, 200)
NAV_LOGO = (235, 235, 235)
