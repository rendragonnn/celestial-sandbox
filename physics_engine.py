"""
physics_engine.py – Core physics simulation engine.

Implements Newton's Law of Universal Gravitation, velocity-Verlet
integration, collision detection/merging, and center-of-mass computation.
"""

import math
from vector_math import (
    vec_add, vec_sub, vec_scale, vec_magnitude,
    vec_normalize, vec_distance, vec_distance_sq,
)
from config import G, SOFTENING, MIN_DISTANCE
from body import CelestialBody
from utils import brighten_color


class PhysicsEngine:
    """
    Handles all physics computations for the simulation.

    Responsibilities:
        • Compute pairwise gravitational forces   (Newton's law)
        • Integrate motion using velocity-Verlet   (stable, symplectic)
        • Detect and resolve collisions            (inelastic merging)
        • Track system-level quantities            (center of mass, energy)
    """

    def __init__(self):
        self.bodies = []           # list[CelestialBody]
        self.total_energy = 0.0
        self.center_of_mass = (0.0, 0.0)
        # For debug visualization: list of (bodyA_pos, bodyB_pos, force_mag)
        self.force_pairs = []

    # ── Public API ────────────────────────────────────────────────────────

    def add_body(self, body):
        """Add a CelestialBody to the simulation."""
        self.bodies.append(body)

    def remove_body(self, body):
        """Remove a body from the simulation."""
        if body in self.bodies:
            self.bodies.remove(body)

    def clear(self):
        """Remove all bodies."""
        self.bodies.clear()

    def step(self, dt):
        """
        Advance the simulation by one timestep *dt*.

        Uses velocity-Verlet integration:
            1. Compute forces / accelerations
            2. Half-step velocity
            3. Full-step position
            4. Recompute forces / accelerations
            5. Half-step velocity (second half)
            6. Handle collisions
            7. Update trails & system-level stats
        """
        if not self.bodies:
            return

        # 1) Compute initial accelerations
        self._compute_forces()

        for b in self.bodies:
            # 2) Half-step velocity:  v += ½ a dt
            b.velocity = vec_add(b.velocity, vec_scale(b.acceleration, 0.5 * dt))
            # 3) Full-step position:  x += v dt
            b.position = vec_add(b.position, vec_scale(b.velocity, dt))

        # 4) Recompute accelerations at new positions
        self._compute_forces()

        for b in self.bodies:
            # 5) Second half-step velocity
            b.velocity = vec_add(b.velocity, vec_scale(b.acceleration, 0.5 * dt))
            # 6) Record trail
            b.update_trail()

        # 7) Collisions
        self._handle_collisions()

        # 8) System stats
        self._compute_center_of_mass()

    # ── Gravity ───────────────────────────────────────────────────────────

    def _compute_forces(self):
        """
        Compute gravitational acceleration on every body using Newton's law:
            F = G * m1 * m2 / r²   (with softening)

        Stores debug force pairs for visualization.
        """
        n = len(self.bodies)
        self.force_pairs = []

        # Reset accelerations
        for b in self.bodies:
            b.acceleration = (0.0, 0.0)

        for i in range(n):
            for j in range(i + 1, n):
                bi = self.bodies[i]
                bj = self.bodies[j]

                diff = vec_sub(bj.position, bi.position)
                dist_sq = vec_distance_sq(bi.position, bj.position)
                dist_sq = max(dist_sq, MIN_DISTANCE * MIN_DISTANCE)

                # Softened distance
                dist = math.sqrt(dist_sq + SOFTENING * SOFTENING)

                # Force magnitude: F = G * m1 * m2 / dist²
                force_mag = G * bi.mass * bj.mass / (dist * dist)

                # Direction unit vector from i → j
                direction = vec_normalize(diff)

                # Acceleration contributions (F = ma → a = F/m)
                acc_i = vec_scale(direction, force_mag / bi.mass)
                acc_j = vec_scale(direction, -force_mag / bj.mass)

                bi.acceleration = vec_add(bi.acceleration, acc_i)
                bj.acceleration = vec_add(bj.acceleration, acc_j)

                # Store for debug rendering
                self.force_pairs.append(
                    (bi.position, bj.position, force_mag)
                )

    # ── Collisions ────────────────────────────────────────────────────────

    def _handle_collisions(self):
        """
        Detect overlapping bodies and merge them.

        Merging conserves momentum and combines masses.
        The larger body absorbs the smaller one.
        """
        to_remove = set()
        n = len(self.bodies)

        for i in range(n):
            if i in to_remove:
                continue
            for j in range(i + 1, n):
                if j in to_remove:
                    continue
                bi = self.bodies[i]
                bj = self.bodies[j]

                dist = vec_distance(bi.position, bj.position)
                if dist < (bi.radius + bj.radius):
                    # Merge: the heavier body absorbs the lighter one
                    if bi.mass >= bj.mass:
                        self._merge(bi, bj)
                        to_remove.add(j)
                    else:
                        self._merge(bj, bi)
                        to_remove.add(i)
                        break  # bi is gone; stop checking against it

        # Remove absorbed bodies (iterate in reverse to keep indices valid)
        for idx in sorted(to_remove, reverse=True):
            self.bodies.pop(idx)

    @staticmethod
    def _merge(survivor, absorbed):
        """
        Merge *absorbed* into *survivor*, conserving linear momentum.

        p_total = m1*v1 + m2*v2
        v_new   = p_total / (m1 + m2)
        """
        total_mass = survivor.mass + absorbed.mass

        # Conservation of momentum
        p = vec_add(
            vec_scale(survivor.velocity, survivor.mass),
            vec_scale(absorbed.velocity, absorbed.mass),
        )
        survivor.velocity = vec_scale(p, 1.0 / total_mass)

        # Weighted position (COM of the two)
        survivor.position = vec_scale(
            vec_add(
                vec_scale(survivor.position, survivor.mass),
                vec_scale(absorbed.position, absorbed.mass),
            ),
            1.0 / total_mass,
        )

        # Update mass and radius (volume-preserving merge)
        survivor.mass = total_mass
        survivor.radius = math.pow(
            survivor.radius ** 3 + absorbed.radius ** 3, 1.0 / 3.0
        )

        # Slightly brighten color on merge for visual feedback
        survivor.glow_color = brighten_color(survivor.color, 1.5)

    # ── System Statistics ─────────────────────────────────────────────────

    def _compute_center_of_mass(self):
        """Compute the center of mass of the entire system."""
        if not self.bodies:
            self.center_of_mass = (0.0, 0.0)
            return

        total_mass = sum(b.mass for b in self.bodies)
        if total_mass == 0:
            self.center_of_mass = (0.0, 0.0)
            return

        cx = sum(b.position[0] * b.mass for b in self.bodies) / total_mass
        cy = sum(b.position[1] * b.mass for b in self.bodies) / total_mass
        self.center_of_mass = (cx, cy)

    def total_system_mass(self):
        """Return the sum of all body masses."""
        return sum(b.mass for b in self.bodies)

    def body_count(self):
        """Return the number of bodies."""
        return len(self.bodies)

    def get_body_at(self, world_pos, threshold=20):
        """
        Return the body closest to *world_pos* within *threshold*
        world-units, or None.
        """
        best = None
        best_dist = threshold
        for b in self.bodies:
            d = vec_distance(b.position, world_pos)
            if d < best_dist:
                best_dist = d
                best = b
        return best
