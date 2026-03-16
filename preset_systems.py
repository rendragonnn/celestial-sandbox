"""
preset_systems.py – Pre-built simulation scenarios.

Each preset returns a list of CelestialBody instances ready to add to
the physics engine.

Presets:
    1 – Binary Star System
    2 – Solar System
    3 – Chaotic Cluster
    4 – Spiral Galaxy
    5 – Random Universe
"""

import math
import random

from body import CelestialBody
from galaxy_generator import GalaxyGenerator
from config import G


def binary_star_system():
    """
    Preset 1: Two stars orbiting their common center of mass,
    with a few planets around each.
    """
    bodies = []

    mass_a = 12000
    mass_b = 10000
    sep = 250  # separation

    # Orbital velocity for circular binary orbit
    # v = sqrt(G * M_other / (sep * (1 + M_other/M_self)))  -- simplified
    v_a = math.sqrt(G * mass_b * mass_b / ((mass_a + mass_b) * sep))
    v_b = math.sqrt(G * mass_a * mass_a / ((mass_a + mass_b) * sep))

    # Star A (left)
    star_a = CelestialBody(-sep / 2, 0, 0, v_a, mass=mass_a, body_type="Star")
    bodies.append(star_a)

    # Star B (right)
    star_b = CelestialBody(sep / 2, 0, 0, -v_b, mass=mass_b, body_type="Star")
    bodies.append(star_b)

    # A few circumbinary planets
    for i, r in enumerate([400, 480, 560]):
        v_orb = math.sqrt(G * (mass_a + mass_b) / r)
        angle = random.uniform(0, 2 * math.pi)
        px = math.cos(angle) * r
        py = math.sin(angle) * r
        vx = -math.sin(angle) * v_orb
        vy = math.cos(angle) * v_orb
        bodies.append(CelestialBody(px, py, vx, vy, body_type="Planet"))

    return bodies


def solar_system():
    """
    Preset 2: A central star with planets in roughly circular orbits.
    """
    bodies = []

    sun_mass = 20000
    sun = CelestialBody(0, 0, 0, 0, mass=sun_mass, body_type="Star")
    bodies.append(sun)

    planet_data = [
        # (distance, mass, type, color)
        (80,   40,   "Dwarf Planet", (180, 160, 140)),   # Mercury-like
        (130,  120,  "Planet",       (220, 180, 100)),    # Venus-like
        (190,  150,  "Planet",       (80, 160, 230)),     # Earth-like
        (250,  100,  "Planet",       (200, 100, 80)),     # Mars-like
        (360,  1500, "Gas Giant",    (210, 180, 130)),    # Jupiter-like
        (470,  1200, "Gas Giant",    (210, 200, 160)),    # Saturn-like
        (580,  800,  "Gas Giant",    (160, 210, 230)),    # Uranus-like
        (680,  900,  "Gas Giant",    (80, 100, 220)),     # Neptune-like
    ]

    for dist, mass, btype, color in planet_data:
        v_orb = math.sqrt(G * sun_mass / dist)
        angle = random.uniform(0, 2 * math.pi)
        px = math.cos(angle) * dist
        py = math.sin(angle) * dist
        vx = -math.sin(angle) * v_orb
        vy = math.cos(angle) * v_orb
        planet = CelestialBody(px, py, vx, vy, mass=mass, body_type=btype,
                               color=color)
        bodies.append(planet)

    return bodies


def chaotic_cluster():
    """
    Preset 3: A dense cluster of bodies with random velocities
    that interact chaotically.
    """
    bodies = []
    for _ in range(30):
        x = random.gauss(0, 120)
        y = random.gauss(0, 120)
        vx = random.gauss(0, 3)
        vy = random.gauss(0, 3)
        btype = random.choice(["Planet", "Planet", "Gas Giant", "Dwarf Planet"])
        bodies.append(CelestialBody(x, y, vx, vy, body_type=btype))
    return bodies


def spiral_galaxy():
    """
    Preset 4: A procedurally generated spiral galaxy.
    """
    return GalaxyGenerator.generate(
        center=(0, 0),
        num_bodies=80,
        arms=3,
        spread=0.5,
        radius_min=60,
        radius_max=500,
        central_mass=80000,
        central_type="Black Hole",
    )


def random_universe():
    """
    Preset 5: Scattered bodies across a large area with various types.
    """
    bodies = []
    types = ["Planet", "Gas Giant", "Dwarf Planet", "Star"]
    for _ in range(40):
        x = random.uniform(-600, 600)
        y = random.uniform(-400, 400)
        vx = random.gauss(0, 2)
        vy = random.gauss(0, 2)
        btype = random.choice(types)
        bodies.append(CelestialBody(x, y, vx, vy, body_type=btype))

    # Add a random black hole somewhere
    bh_x = random.uniform(-200, 200)
    bh_y = random.uniform(-200, 200)
    bodies.append(CelestialBody.create_black_hole(bh_x, bh_y))

    return bodies


# ── Preset registry ───────────────────────────────────────────────────────────

PRESETS = {
    1: ("Binary Star System", binary_star_system),
    2: ("Solar System",       solar_system),
    3: ("Chaotic Cluster",    chaotic_cluster),
    4: ("Spiral Galaxy",      spiral_galaxy),
    5: ("Random Universe",    random_universe),
}
