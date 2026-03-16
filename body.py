"""
body.py – CelestialBody class representing a single gravitational body.

Each body carries its own position, velocity, acceleration, mass, visual
properties, and orbit trail history.
"""

import random
from config import BODY_TYPES, DEFAULT_BODY_TYPE, MAX_TRAIL_LENGTH
from utils import generate_id, brighten_color
from vector_math import vec_magnitude, vec_sub


class CelestialBody:
    """
    Represents a single celestial body in the simulation.

    Attributes:
        id          – unique identifier
        body_type   – string label ("Planet", "Star", etc.)
        position    – (x, y) world position
        velocity    – (x, y) velocity
        acceleration – (x, y) current-frame acceleration
        mass        – scalar mass
        radius      – visual/collision radius
        color       – RGB tuple
        glow_color  – brightened color used for glow rendering
        trail       – list of past positions for orbit trail
        is_selected – whether this body is currently selected by the user
    """

    def __init__(self, x, y, vx=0.0, vy=0.0, mass=None, radius=None,
                 color=None, body_type=None):
        # Assign type and derive defaults from type presets
        self.body_type = body_type or DEFAULT_BODY_TYPE
        preset = BODY_TYPES.get(self.body_type, BODY_TYPES[DEFAULT_BODY_TYPE])

        self.id = generate_id()
        self.position = (float(x), float(y))
        self.velocity = (float(vx), float(vy))
        self.acceleration = (0.0, 0.0)

        # Use provided values or sample from the preset ranges
        if mass is not None:
            self.mass = float(mass)
        else:
            lo, hi = preset["mass_range"]
            self.mass = random.uniform(lo, hi)

        if radius is not None:
            self.radius = float(radius)
        else:
            lo, hi = preset["radius_range"]
            self.radius = random.uniform(lo, hi)

        if color is not None:
            self.color = color
        else:
            self.color = random.choice(preset["colors"])

        self.glow_color = brighten_color(self.color, 1.4)
        self.trail = []
        self.is_selected = False

        # Accumulated force for the current frame (reset each tick)
        self._force = (0.0, 0.0)

    # ── Helpers ───────────────────────────────────────────────────────────

    def speed(self):
        """Return the scalar speed of this body."""
        return vec_magnitude(self.velocity)

    def distance_to(self, other):
        """Return the distance to another body."""
        return vec_magnitude(vec_sub(other.position, self.position))

    def kinetic_energy(self):
        """Return ½mv²."""
        return 0.5 * self.mass * (self.speed() ** 2)

    def update_trail(self):
        """Append current position to the trail and trim old entries."""
        self.trail.append(self.position)
        if len(self.trail) > MAX_TRAIL_LENGTH:
            self.trail = self.trail[-MAX_TRAIL_LENGTH:]

    def clear_trail(self):
        """Clear the orbit trail."""
        self.trail.clear()

    # ── Factory Methods ───────────────────────────────────────────────────

    @staticmethod
    def create_star(x, y, vx=0.0, vy=0.0, mass=None):
        """Convenience factory for a Star body."""
        return CelestialBody(x, y, vx, vy, mass=mass or 15000, body_type="Star")

    @staticmethod
    def create_planet(x, y, vx=0.0, vy=0.0, mass=None):
        """Convenience factory for a Planet body."""
        return CelestialBody(x, y, vx, vy, mass=mass, body_type="Planet")

    @staticmethod
    def create_gas_giant(x, y, vx=0.0, vy=0.0, mass=None):
        """Convenience factory for a Gas Giant body."""
        return CelestialBody(x, y, vx, vy, mass=mass, body_type="Gas Giant")

    @staticmethod
    def create_dwarf_planet(x, y, vx=0.0, vy=0.0, mass=None):
        """Convenience factory for a Dwarf Planet body."""
        return CelestialBody(x, y, vx, vy, mass=mass, body_type="Dwarf Planet")

    @staticmethod
    def create_black_hole(x, y, vx=0.0, vy=0.0, mass=None):
        """Convenience factory for a Black Hole body."""
        return CelestialBody(x, y, vx, vy, mass=mass or 100000, body_type="Black Hole")

    def __repr__(self):
        return (f"<Body #{self.id} {self.body_type} "
                f"pos=({self.position[0]:.0f},{self.position[1]:.0f}) "
                f"mass={self.mass:.0f}>")
