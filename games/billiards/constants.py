"""Billiards layout, timing and palette (view choices only).

Touch-first: aim by dragging on the cloth, shoot by pulling the power gauge down and
letting go. No keyboard or right click needed.
"""
from engine import sidebar, theme

from . import physics

NAV_WIDTH = sidebar.WIDTH
RAIL = 24
PLAY_X, PLAY_Y = NAV_WIDTH + 48, 174          # top-left of the cloth on screen
TABLE_X, TABLE_Y = PLAY_X - RAIL, PLAY_Y - RAIL
TABLE_W, TABLE_H = int(physics.W) + 2 * RAIL, int(physics.H) + 2 * RAIL
BAR_X, BAR_W = TABLE_X + TABLE_W + 14, 34     # power gauge, right of the table
HEADER_Y = 34
POCKET_RADIUS = 15

CUE_LENGTH = 250
CUE_GAP = 10              # between cue tip and ball at zero power
CUE_PULL = 70             # extra pull-back at full power
MIN_POWER = 0.03          # releasing the gauge below this cancels the shot
AI_THINK = 0.5            # seconds before the AI starts aiming
AI_AIM_TIME = 0.6         # the AI's cue swings to its angle...
AI_CHARGE_TIME = 0.45     # ...then pulls back to its power
POT_ANIM = 0.25           # seconds a potted ball takes to sink

ACCENT = theme.PINK
COLOR_CLOTH = (26, 98, 80)
COLOR_CLOTH_DARK = (20, 80, 66)
COLOR_CUSHION = (18, 74, 60)
COLOR_RAIL = (74, 50, 40)
COLOR_RAIL_EDGE = (52, 34, 28)
COLOR_DIAMOND = (220, 205, 170)
COLOR_POCKET = (8, 8, 10)
COLOR_SHADOW = (10, 30, 24)
COLOR_AIM = (235, 240, 245)
COLOR_GHOST = (235, 240, 245)
COLOR_CUE_TIP = (90, 150, 200)
COLOR_CUE_FERRULE = (235, 230, 215)
COLOR_CUE_SHAFT = (205, 160, 100)
COLOR_CUE_BUTT = (70, 40, 30)
COLOR_TEXT = theme.TEXT
COLOR_TEXT_SOFT = theme.TEXT_SOFT
COLOR_TEXT_DIM = theme.TEXT_DIM
COLOR_PANEL = theme.SURFACE_RAISED
COLOR_PANEL_ACTIVE = theme.SURFACE_HOVER
COLOR_CARD = (*theme.SURFACE, 235)
COLOR_BORDER = theme.BORDER
POWER_LOW, POWER_MID, POWER_HIGH = theme.GREEN, theme.YELLOW, theme.RED

# Standard pool colors: 1 yellow, 2 blue, 3 red, 4 purple, 5 orange, 6 green, 7 maroon, 8 black.
BALL_COLORS = {
    1: (240, 196, 40), 2: (40, 80, 190), 3: (210, 50, 45), 4: (110, 50, 150),
    5: (240, 120, 30), 6: (30, 130, 70), 7: (130, 40, 40), 8: (20, 20, 24),
}
