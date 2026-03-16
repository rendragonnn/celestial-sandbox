"""
camera.py – Camera system for panning, zooming, and following bodies.

Converts between world coordinates and screen (pixel) coordinates.
Supports smooth zoom, pan, and tracking of a selected body or the
system center of mass.
"""

from config import WINDOW_WIDTH, WINDOW_HEIGHT
from vector_math import vec_add, vec_sub, vec_scale, vec_lerp
from utils import clamp


class Camera:
    """
    2D camera with zoom, pan, and follow capabilities.

    World-space origin starts at the center of the screen.

    Coordinate conversion:
        screen = (world - offset) * zoom + screen_center
        world  = (screen - screen_center) / zoom + offset
    """

    ZOOM_MIN = 0.05
    ZOOM_MAX = 10.0
    ZOOM_SPEED = 0.1
    PAN_SMOOTHING = 0.08   # lerp factor for smooth follow

    def __init__(self, width=WINDOW_WIDTH, height=WINDOW_HEIGHT):
        self.width = width
        self.height = height
        self.offset = (0.0, 0.0)       # world-space offset (what is at center)
        self.zoom = 1.0
        self.target_zoom = 1.0

        # Follow mode
        self.follow_body = None        # CelestialBody or None
        self.follow_com = False        # follow center-of-mass instead

        # Panning state
        self._panning = False
        self._pan_start = (0, 0)
        self._pan_offset_start = (0.0, 0.0)

    # ── Coordinate Conversion ─────────────────────────────────────────────

    @property
    def screen_center(self):
        return (self.width / 2.0, self.height / 2.0)

    def world_to_screen(self, world_pos):
        """Convert a world position to screen coordinates."""
        cx, cy = self.screen_center
        sx = (world_pos[0] - self.offset[0]) * self.zoom + cx
        sy = (world_pos[1] - self.offset[1]) * self.zoom + cy
        return (sx, sy)

    def screen_to_world(self, screen_pos):
        """Convert a screen position to world coordinates."""
        cx, cy = self.screen_center
        wx = (screen_pos[0] - cx) / self.zoom + self.offset[0]
        wy = (screen_pos[1] - cy) / self.zoom + self.offset[1]
        return (wx, wy)

    def world_radius_to_screen(self, radius):
        """Scale a world-space radius to screen pixels."""
        return max(1, radius * self.zoom)

    # ── Zoom ──────────────────────────────────────────────────────────────

    def zoom_in(self, amount=1):
        """Zoom in (increase zoom level)."""
        self.target_zoom *= (1 + self.ZOOM_SPEED * amount)
        self.target_zoom = clamp(self.target_zoom, self.ZOOM_MIN, self.ZOOM_MAX)

    def zoom_out(self, amount=1):
        """Zoom out (decrease zoom level)."""
        self.target_zoom /= (1 + self.ZOOM_SPEED * amount)
        self.target_zoom = clamp(self.target_zoom, self.ZOOM_MIN, self.ZOOM_MAX)

    def zoom_at(self, screen_pos, zoom_in=True):
        """
        Zoom towards (or away from) a specific screen position,
        keeping that point visually stationary.
        """
        world_before = self.screen_to_world(screen_pos)

        if zoom_in:
            self.zoom_in()
        else:
            self.zoom_out()

        # Apply zoom immediately for the correction
        self.zoom = self.target_zoom

        world_after = self.screen_to_world(screen_pos)
        # Adjust offset so the point under the cursor stays put
        self.offset = vec_sub(self.offset, vec_sub(world_after, world_before))

    # ── Pan ───────────────────────────────────────────────────────────────

    def start_pan(self, screen_pos):
        """Begin a pan drag from screen_pos."""
        self._panning = True
        self._pan_start = screen_pos
        self._pan_offset_start = self.offset
        # Disable follow while manually panning
        self.follow_body = None
        self.follow_com = False

    def update_pan(self, screen_pos):
        """Update the pan offset during a drag."""
        if not self._panning:
            return
        dx = (screen_pos[0] - self._pan_start[0]) / self.zoom
        dy = (screen_pos[1] - self._pan_start[1]) / self.zoom
        self.offset = vec_sub(self._pan_offset_start, (dx, dy))

    def end_pan(self):
        """Finish a pan drag."""
        self._panning = False

    # ── Follow ────────────────────────────────────────────────────────────

    def set_follow_body(self, body):
        """Start following a specific body."""
        self.follow_body = body
        self.follow_com = False

    def set_follow_com(self, enabled=True):
        """Follow the system center of mass."""
        self.follow_com = enabled
        self.follow_body = None

    def stop_following(self):
        """Stop following any target."""
        self.follow_body = None
        self.follow_com = False

    # ── Update ────────────────────────────────────────────────────────────

    def update(self, center_of_mass=(0, 0)):
        """
        Called once per frame.

        Smoothly interpolates zoom and follow target.
        """
        # Smooth zoom
        self.zoom += (self.target_zoom - self.zoom) * 0.15

        # Follow a body
        if self.follow_body is not None:
            # Check if body is still alive (still has an id attribute)
            target = self.follow_body.position
            self.offset = vec_lerp(self.offset, target, self.PAN_SMOOTHING)

        elif self.follow_com:
            self.offset = vec_lerp(self.offset, center_of_mass, self.PAN_SMOOTHING)

    def reset(self):
        """Reset camera to default state."""
        self.offset = (0.0, 0.0)
        self.zoom = 1.0
        self.target_zoom = 1.0
        self.follow_body = None
        self.follow_com = False
