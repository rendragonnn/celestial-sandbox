"""
galaxy_generator.py – Procedural galaxy-like system generator.

Creates a spiral-arm distribution of bodies orbiting a central
massive object (star or black hole).
"""

import math
import random

from body import CelestialBody
from vector_math import vec_from_angle, vec_magnitude, vec_add
from config import G


class GalaxyGenerator:
    """
    Generates a rotating galaxy structure with spiral arms, a massive
    central body, and orbiting smaller bodies.
    """

    @staticmethod
    def generate(center=(0, 0), num_bodies=80, arms=3, spread=0.6,
                 radius_min=80, radius_max=600, central_mass=80000,
                 central_type="Black Hole"):
        """
        Generate a galaxy-like system.

        Args:
            center:        (x, y) center of the galaxy
            num_bodies:    number of orbiting bodies to create
            arms:          number of spiral arms
            spread:        angular spread of each arm (radians)
            radius_min:    minimum orbit radius
            radius_max:    maximum orbit radius
            central_mass:  mass of the central body
            central_type:  type of the central body

        Returns:
            list[CelestialBody]
        """
        bodies = []

        # Central body
        central = CelestialBody(
            center[0], center[1], 0, 0,
            mass=central_mass,
            body_type=central_type,
        )
        bodies.append(central)

        for i in range(num_bodies):
            # Pick a spiral arm
            arm_index = i % arms
            base_angle = (2 * math.pi / arms) * arm_index

            # Radius along the arm (biased toward outer regions)
            t = random.random()
            radius = radius_min + (radius_max - radius_min) * (t ** 0.7)

            # Spiral twist: angle increases with radius
            twist = radius / radius_max * math.pi * 1.5
            angle = base_angle + twist + random.gauss(0, spread)

            # Position
            offset = vec_from_angle(angle, radius)
            px = center[0] + offset[0]
            py = center[1] + offset[1]

            # Circular orbital velocity: v = sqrt(G * M / r)
            orbital_speed = math.sqrt(G * central_mass / max(radius, 1))

            # Velocity perpendicular to the radius vector (tangential)
            vel_angle = angle + math.pi / 2  # 90° ahead
            vx = math.cos(vel_angle) * orbital_speed
            vy = math.sin(vel_angle) * orbital_speed

            # Determine body type based on distance
            if radius < radius_max * 0.3:
                btype = random.choice(["Planet", "Planet", "Dwarf Planet"])
            elif radius < radius_max * 0.7:
                btype = random.choice(["Planet", "Gas Giant", "Dwarf Planet"])
            else:
                btype = random.choice(["Dwarf Planet", "Dwarf Planet", "Planet"])

            body = CelestialBody(px, py, vx, vy, body_type=btype)
            # Scale down mass for galaxy bodies
            body.mass *= 0.3
            body.radius *= 0.7
            bodies.append(body)

        return bodies
