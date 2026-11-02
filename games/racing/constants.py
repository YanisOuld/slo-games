"""Racing tuning (physics, race) and palette.

World units are pixels of the track view. Physics runs at a fixed timestep so a run
is reproducible (same controls = same lap), which a learning driver will need.
"""
from engine import constants as screen
from engine import sidebar, theme

STEP_DT = 1 / 60
LAPS = 3
COUNTDOWN = 3.0          # seconds before GO

NAV_WIDTH = sidebar.WIDTH
VIEW_X = NAV_WIDTH
VIEW_W = screen.SCREEN_WIDTH - NAV_WIDTH
VIEW_H = screen.SCREEN_HEIGHT
VIEW_MARGIN = 24

# -- car physics --
CAR_LENGTH, CAR_WIDTH = 24, 13
CAR_RADIUS = 8           # collision circle
ENGINE = 520             # px/s² at full throttle
BRAKE = 900              # px/s² when braking while moving forward
REVERSE = 260
MAX_REVERSE = 90         # px/s
DRAG = 1.55              # air drag (1/s): top speed ≈ ENGINE / DRAG
ROLLING = 40             # px/s² rolling resistance
GRIP = 9.0               # how fast sideways sliding dies out (1/s)
HANDBRAKE_GRIP = 1.6     # much less grip: the rear slides, you drift
HANDBRAKE_DRAG = 0.9
STEER_RATE = 3.3         # rad/s at full lock
STEER_FULL_SPEED = 140   # px/s: below this, steering is proportionally weaker
WALL_BOUNCE = 0.25       # fraction of the into-wall speed bounced back
WALL_SCRAPE = 0.82       # along-wall speed kept when touching a wall
DRIFT_SPEED = 70         # sideways px/s above which the tyres leave skid marks

COLLISION_WINDOW = 14    # centerline samples checked around the car for walls
SENSOR_ANGLES = (-90, -50, -25, 0, 25, 50, 90)  # degrees, relative to heading
SENSOR_RANGE = 240       # px
SENSOR_WINDOW = 45       # centerline samples searched by the rays

# -- palette --
ACCENT = theme.CYAN
COLOR_GROUND = theme.BG
COLOR_GROUND_DOT = (22, 24, 34)
COLOR_ASPHALT = (44, 47, 62)
COLOR_EDGE = (70, 75, 98)
COLOR_KERB_A = theme.RED
COLOR_KERB_B = theme.LIGHT
COLOR_CENTER = (60, 64, 84)
COLOR_SKID = (30, 32, 42)
COLOR_CAR = theme.CYAN
COLOR_CAR_DARK = (40, 120, 140)
COLOR_GLASS = (20, 26, 40)
COLOR_WHEEL = (12, 12, 16)
COLOR_GHOST = theme.LIGHT
COLOR_SENSOR_NEAR = theme.RED
COLOR_SENSOR_FAR = theme.GREEN
COLOR_TEXT = theme.TEXT
COLOR_TEXT_SOFT = theme.TEXT_SOFT
COLOR_SHADE = (*theme.BG, 190)
COLOR_CARD = (*theme.SURFACE, 240)
COLOR_CARD_BORDER = theme.BORDER
