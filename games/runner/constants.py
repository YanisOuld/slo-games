"""Runner tuning (physics, world generation) and palette.

World units are pixels; y grows downward like the screen. Physics runs at a fixed
timestep so a run is reproducible (same seed + same actions = same run), which is
what a reinforcement learning agent will need later.
"""
from engine import constants as screen
from engine import theme

STEP_DT = 1 / 60  # seconds per physics step

GROUND_Y = 470             # top of the ground
PLAYER_SCREEN_X = 180      # the camera keeps the player at this screen x
PLAYER_W = 34
PLAYER_H = 50
PLAYER_DUCK_H = 28

GRAVITY = 2600             # px/s²
JUMP_VELOCITY = 860        # px/s, upward
JUMP_CUT_GRAVITY = 2.2     # gravity multiplier when jump is released while rising (short hop)
FAST_FALL_GRAVITY = 2.5    # gravity multiplier when ducking in the air
COYOTE_TIME = 0.08         # seconds you can still jump after running off an edge

START_SPEED = 380          # px/s
MAX_SPEED = 900
ACCELERATION = 7           # px/s gained per second

HITBOX_MARGIN = 4          # obstacles hit a slightly smaller box: forgiving near misses
PLATFORM_THICKNESS = 16
COIN_RADIUS = 9
COIN_POINTS = 10
PX_PER_METER = 10

SPAWN_AHEAD = screen.SCREEN_WIDTH * 1.5   # world is generated this far ahead of the player
DESPAWN_BEHIND = 200                      # and dropped this far behind the camera

# Zones: each new zone may unlock a new enemy. The first lasts ZONE_FIRST_LENGTH_M
# meters, and each next one is ZONE_GROWTH times longer (1000, 1300, 1690, 2197...):
# zones grow exponentially, keeping pace with the ever-faster run.
ZONE_FIRST_LENGTH_M = 1000
ZONE_GROWTH = 1.3

SLIME_W, SLIME_H = 40, 26
SLIME_SPEED = 120          # px/s toward the player, once on screen
STOMP_TOLERANCE = 12       # feet this far below a slime's top still count as a stomp
STOMP_BOUNCE = 650         # px/s upward after a stomp
STOMP_POINTS = 50

DRONE_W, DRONE_H = 46, 22
WAVE_CENTER = 46           # wave drone: bottom edge oscillates around this height above ground
WAVE_AMPLITUDE = 34
WAVE_FREQUENCY = 2.6       # rad/s

# Ceiling spikes: their bottom is this high above the ground. A full jump hits
# them; a tap (up to ~10 frames held) fits underneath.
CEILING_CLEARANCE = 172

MISSILE_W, MISSILE_H = 46, 16
MISSILE_SPEED = 520        # px/s toward the player, on top of the player's own speed
MISSILE_WARNING = 1.0      # seconds the warning shows before launch
MISSILE_LOW_BOTTOM = GROUND_Y - 4    # at the feet: jump
MISSILE_HIGH_BOTTOM = GROUND_Y - 34  # at the head: duck

# -- palette --
# Sky (top, bottom) per zone, cycling once zones run out.
ZONE_SKIES = (
    ((22, 24, 48), (70, 60, 110)),     # dusk
    ((16, 40, 60), (40, 110, 130)),    # teal
    ((50, 20, 40), (150, 70, 70)),     # sunset
    ((14, 14, 22), (40, 40, 70)),      # night
    ((30, 10, 50), (110, 40, 120)),    # neon
    ((40, 30, 10), (150, 110, 50)),    # desert
)
# Shown in the zone banner: what's new in that zone.
ZONE_NEWS = {
    2: "Nouveau : drones",
    3: "Nouveau : slimes (saute-leur dessus !)",
    4: "Nouveau : drones ondulants",
    5: "Nouveau : plafonds à pics (petit saut !)",
    6: "Nouveau : missiles",
    7: "Tout se mélange !",
}
HILLS_FAR = (48, 46, 86)
HILLS_NEAR = (36, 36, 66)
GROUND_TOP = (96, 200, 120)
GROUND_DIRT = (60, 46, 52)
GROUND_DIRT_DARK = (48, 36, 42)
PLATFORM = (150, 120, 200)
PLATFORM_TOP = (190, 160, 240)
BLOCK = (200, 120, 70)
BLOCK_DARK = (140, 80, 50)
DRONE = (200, 205, 220)
DRONE_LIGHT = (240, 70, 80)
WAVE_DRONE = (240, 170, 90)
SLIME = (120, 220, 90)
SLIME_DARK = (70, 160, 60)
CEILING = (40, 34, 50)
SPIKE = (200, 200, 215)
MISSILE = (180, 180, 195)
MISSILE_NOSE = (230, 70, 70)
FLAME = (255, 170, 60)
WARNING = (240, 60, 60)
COIN = (250, 210, 70)
COIN_SHINE = (255, 245, 180)
PLAYER = (90, 190, 250)
PLAYER_DARK = (50, 120, 190)
PLAYER_EYE = (20, 20, 30)

HUD_TEXT = theme.TEXT
HUD_DIM = theme.TEXT_SOFT
OVERLAY_SHADE = (0, 0, 0, 150)
