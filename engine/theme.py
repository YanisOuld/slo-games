"""Shared color palette: every screen draws from it so the app looks like one app.

Dark surfaces for the interface, light and bright colors for what you play with.
Each game picks ONE accent (the same as its card in the menu).
"""

# -- dark surfaces, from back to front --
BG = (14, 15, 22)               # app background
SURFACE = (20, 22, 32)          # side panels, boards
SURFACE_RAISED = (30, 33, 46)   # buttons, cards, empty cells
SURFACE_HOVER = (42, 46, 64)
BORDER = (48, 52, 72)

# -- text --
TEXT = (236, 238, 245)          # titles
TEXT_SOFT = (196, 200, 215)     # body text
TEXT_DIM = (130, 135, 160)      # help, secondary info

# -- light: game pieces that must stand out on dark boards --
LIGHT = (226, 230, 240)

# -- accents (one per game) --
BLUE = (100, 160, 255)     # Binairo
GREEN = (120, 220, 120)    # Snake
RED = (240, 100, 100)      # Démineur
YELLOW = (250, 210, 70)    # Runner
PURPLE = (170, 130, 255)   # menu / brand

BUTTON_RADIUS = 8
