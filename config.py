"""
config.py – Global constants and configuration for Celestial Sandbox.

Contains window settings, physics constants, color palette, body type
presets, and simulation defaults.
"""

import math

# ─── Window Settings ─────────────────────────────────────────────────────────
WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 720
FPS = 60
TITLE = "Celestial Sandbox – Advanced Orbital Mechanics Simulator"

# ─── Physics Constants ────────────────────────────────────────────────────────
G = 6.674           # Gravitational constant (scaled for simulation)
SOFTENING = 5.0     # Softening factor to prevent division-by-zero singularities
MIN_DISTANCE = 10.0 # Minimum distance for force computation
DT_BASE = 0.1       # Base timestep
MAX_TRAIL_LENGTH = 300  # Maximum trail history per body
SHATTER_THRESHOLD = 45.0 # Minimum relative velocity to trigger shatter instead of merge

# ─── Color Palette ────────────────────────────────────────────────────────────
COLOR_BLACK      = (0, 0, 0)
COLOR_WHITE      = (255, 255, 255)
COLOR_DARK_GRAY  = (20, 20, 30)
COLOR_LIGHT_GRAY = (140, 140, 160)
COLOR_YELLOW     = (255, 220, 80)
COLOR_ORANGE     = (255, 140, 50)
COLOR_RED        = (255, 60, 60)
COLOR_BLUE       = (80, 130, 255)
COLOR_CYAN       = (80, 230, 255)
COLOR_GREEN      = (80, 220, 120)
COLOR_PURPLE     = (170, 80, 255)
COLOR_PINK       = (255, 100, 180)
COLOR_DEEP_BLUE  = (10, 10, 35)

# ─── Background ──────────────────────────────────────────────────────────────
BG_COLOR = COLOR_DEEP_BLUE
STAR_COUNT = 250            # Number of background stars
STAR_LAYER_COUNT = 3        # Parallax layers

# ─── Body Type Definitions ────────────────────────────────────────────────────
# Each type: (mass_min, mass_max, radius_min, radius_max, colors)
BODY_TYPES = {
    "Planet": {
        "mass_range": (50, 500),
        "radius_range": (4, 10),
        "colors": [
            (100, 180, 255),  # icy blue
            (180, 120, 80),   # rocky brown
            (120, 200, 120),  # green
            (200, 160, 100),  # sandy
        ],
    },
    "Gas Giant": {
        "mass_range": (800, 3000),
        "radius_range": (12, 22),
        "colors": [
            (220, 180, 120),  # jupiter gold
            (200, 170, 140),  # saturn beige
            (140, 180, 210),  # uranus blue
            (80, 100, 200),   # neptune blue
        ],
    },
    "Dwarf Planet": {
        "mass_range": (10, 50),
        "radius_range": (2, 5),
        "colors": [
            (180, 180, 180),  # gray
            (160, 140, 120),  # brownish
            (200, 200, 220),  # icy
        ],
    },
    "Star": {
        "mass_range": (5000, 30000),
        "radius_range": (20, 35),
        "colors": [
            (255, 240, 180),  # yellow-white
            (255, 200, 100),  # orange star
            (180, 200, 255),  # blue star
            (255, 150, 100),  # red giant
        ],
    },
    "Black Hole": {
        "mass_range": (50000, 200000),
        "radius_range": (15, 25),
        "colors": [
            (20, 0, 40),      # deep void
        ],
    },
    "Asteroid": {
        "mass_range": (1, 5),
        "radius_range": (1, 2),
        "colors": [
            (255, 100, 50),   # fiery red
            (255, 200, 50),   # yellow heat
            (120, 120, 120),  # rocky ash
        ],
    },
}

# ─── Default spawn type ──────────────────────────────────────────────────────
DEFAULT_BODY_TYPE = "Planet"

# ─── Simulation Speed ────────────────────────────────────────────────────────
SPEED_MIN = 0.1
SPEED_MAX = 10.0
SPEED_STEP = 0.2

# ─── Time Warp Tiers ─────────────────────────────────────────────────────────
TIME_WARP_TIERS = [1.0, 10.0, 100.0, 1000.0]

# ─── UI Settings ─────────────────────────────────────────────────────────────
UI_FONT_SIZE = 16
UI_TITLE_FONT_SIZE = 20
UI_PANEL_WIDTH = 260
UI_PANEL_ALPHA = 180
UI_PANEL_COLOR = (15, 15, 30)
UI_TEXT_COLOR = (200, 210, 230)
UI_HIGHLIGHT_COLOR = COLOR_CYAN
UI_MARGIN = 12

# ─── Velocity Arrow ──────────────────────────────────────────────────────────
VELOCITY_ARROW_SCALE = 0.5   # scale factor when dragging to set velocity
VELOCITY_ARROW_COLOR = (255, 100, 100)

# ─── Glow Settings ───────────────────────────────────────────────────────────
GLOW_LAYERS = 8              # number of additive glow rings (enhanced)
GLOW_ALPHA_BASE = 50         # starting alpha for outer glow
GLOW_INNER_ALPHA = 120       # alpha for the inner bright glow
GLOW_OUTER_RADIUS_FACTOR = 8 # outer glow ring spacing in pixels
GLOW_INNER_RADIUS_FACTOR = 0.7  # inner glow as fraction of body radius

# ─── Mini Map Settings ───────────────────────────────────────────────────────
MINIMAP_WIDTH = 180
MINIMAP_HEIGHT = 130
MINIMAP_MARGIN = 10
MINIMAP_BG_ALPHA = 160
MINIMAP_BG_COLOR = (10, 10, 25)
MINIMAP_BORDER_COLOR = (60, 80, 120)
MINIMAP_BODY_MIN_SIZE = 2
MINIMAP_VIEW_COLOR = (80, 200, 255, 100)

# ─── Debug ────────────────────────────────────────────────────────────────────
DEBUG_FORCE_SCALE = 0.002    # scale for drawing force vectors
DEBUG_TEXT_COLOR = (0, 255, 160)
