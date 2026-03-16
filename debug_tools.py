"""
debug_tools.py – Developer debug overlay for the Celestial Sandbox.

Toggled with the D key, this overlay renders force vectors, physics
stats, and per-body diagnostics.
"""

import pygame
from config import (
    WINDOW_WIDTH, DEBUG_FORCE_SCALE, DEBUG_TEXT_COLOR,
)
from vector_math import vec_add, vec_scale, vec_sub, vec_normalize, vec_magnitude


class DebugTools:
    """
    Debug overlay that visualizes force vectors, frame rate, and
    per-body physics data.
    """

    def __init__(self, surface, camera):
        self.surface = surface
        self.camera = camera
        self.enabled = False
        pygame.font.init()
        self.font = pygame.font.SysFont("Consolas", 13)

    def toggle(self):
        """Toggle debug mode on/off."""
        self.enabled = not self.enabled

    # ── Drawing ───────────────────────────────────────────────────────────

    def draw(self, physics_engine, clock, sim_speed):
        """
        Draw the full debug overlay (only when enabled).
        """
        if not self.enabled:
            return

        # ── Force vectors between body pairs ──────────────────────────
        for pos_a, pos_b, force_mag in physics_engine.force_pairs:
            self._draw_force_line(pos_a, pos_b, force_mag)

        # ── Per-body acceleration vectors ─────────────────────────────
        for body in physics_engine.bodies:
            sp = self.camera.world_to_screen(body.position)
            acc_mag = vec_magnitude(body.acceleration)
            if acc_mag > 0.001:
                acc_dir = vec_normalize(body.acceleration)
                end_world = vec_add(
                    body.position,
                    vec_scale(acc_dir, acc_mag * 500),
                )
                ep = self.camera.world_to_screen(end_world)
                pygame.draw.line(
                    self.surface, (255, 200, 0),
                    (int(sp[0]), int(sp[1])),
                    (int(ep[0]), int(ep[1])),
                    1,
                )

        # ── Top-left debug stats ──────────────────────────────────────
        y = 10
        fps = clock.get_fps()
        lines = [
            f"[DEBUG MODE]",
            f"FPS:        {fps:.1f}",
            f"Bodies:     {physics_engine.body_count()}",
            f"Sim Speed:  {sim_speed:.1f}x",
            f"Force Pairs:{len(physics_engine.force_pairs)}",
            f"COM:        ({physics_engine.center_of_mass[0]:.1f}, "
            f"{physics_engine.center_of_mass[1]:.1f})",
        ]
        for line in lines:
            rendered = self.font.render(line, True, DEBUG_TEXT_COLOR)
            self.surface.blit(rendered, (10, y))
            y += 16

    def _draw_force_line(self, pos_a, pos_b, force_mag):
        """
        Draw a thin line between two bodies representing gravitational
        force, with brightness proportional to force magnitude.
        """
        sp_a = self.camera.world_to_screen(pos_a)
        sp_b = self.camera.world_to_screen(pos_b)

        # Clamp brightness by force magnitude
        brightness = min(255, int(force_mag * DEBUG_FORCE_SCALE * 255))
        brightness = max(30, brightness)
        color = (brightness // 3, brightness, brightness // 2)

        pygame.draw.line(
            self.surface, color,
            (int(sp_a[0]), int(sp_a[1])),
            (int(sp_b[0]), int(sp_b[1])),
            1,
        )
