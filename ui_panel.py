"""
ui_panel.py – Heads-Up Display (HUD) panel for the Celestial Sandbox.

Shows simulation statistics, selected-body info, and control hints
in a translucent overlay panel.
"""

import pygame
from config import (
    WINDOW_WIDTH, WINDOW_HEIGHT,
    UI_FONT_SIZE, UI_TITLE_FONT_SIZE, UI_PANEL_WIDTH,
    UI_PANEL_ALPHA, UI_PANEL_COLOR, UI_TEXT_COLOR,
    UI_HIGHLIGHT_COLOR, UI_MARGIN, TIME_WARP_TIERS,
)
from utils import format_number
from vector_math import vec_magnitude, vec_distance


class UIPanel:
    """
    Renders a translucent sidebar panel with simulation statistics,
    selected-body details, and keyboard shortcut hints.
    """

    def __init__(self, surface):
        self.surface = surface
        pygame.font.init()
        self.font = pygame.font.SysFont("Consolas", UI_FONT_SIZE)
        self.title_font = pygame.font.SysFont("Consolas", UI_TITLE_FONT_SIZE, bold=True)
        self.small_font = pygame.font.SysFont("Consolas", UI_FONT_SIZE - 2)

    # ── Drawing Helpers ───────────────────────────────────────────────────

    def _draw_text(self, text, x, y, color=UI_TEXT_COLOR, font=None):
        """Render a single line of text at (x, y)."""
        f = font or self.font
        rendered = f.render(text, True, color)
        self.surface.blit(rendered, (x, y))
        return rendered.get_height()

    def _draw_separator(self, x, y, width):
        """Draw a horizontal separator line."""
        pygame.draw.line(
            self.surface, (60, 60, 80),
            (x, y), (x + width, y), 1,
        )

    # ── Main Draw ─────────────────────────────────────────────────────────

    def draw(self, physics_engine, sim_speed, paused, selected_body=None,
             current_type="Planet", time_warp_index=0):
        """
        Draw the full HUD panel on the right side of the screen.
        """
        panel_x = WINDOW_WIDTH - UI_PANEL_WIDTH
        panel_h = WINDOW_HEIGHT

        # Translucent background
        panel_surf = pygame.Surface((UI_PANEL_WIDTH, panel_h), pygame.SRCALPHA)
        panel_surf.fill((*UI_PANEL_COLOR, UI_PANEL_ALPHA))
        self.surface.blit(panel_surf, (panel_x, 0))

        x = panel_x + UI_MARGIN
        y = UI_MARGIN

        # ── Title ─────────────────────────────────────────────────────
        y += self._draw_text("CELESTIAL SANDBOX", x, y,
                             UI_HIGHLIGHT_COLOR, self.title_font)
        y += 4
        self._draw_separator(x, y, UI_PANEL_WIDTH - UI_MARGIN * 2)
        y += 10

        # ── Simulation Info ───────────────────────────────────────────
        y += self._draw_text("── Simulation ──", x, y, (120, 130, 160))
        y += 4
        status = "PAUSED" if paused else "RUNNING"
        status_color = (255, 100, 100) if paused else (100, 255, 140)
        y += self._draw_text(f"Status:  {status}", x, y, status_color)
        y += self._draw_text(f"Speed:   {sim_speed:.1f}x", x, y)
        y += self._draw_text(f"Bodies:  {physics_engine.body_count()}", x, y)
        total_mass = physics_engine.total_system_mass()
        y += self._draw_text(f"Mass:    {format_number(total_mass)}", x, y)
        com = physics_engine.center_of_mass
        y += self._draw_text(
            f"COM:     ({format_number(com[0])}, {format_number(com[1])})", x, y,
        )
        y += 8

        # ── Time Warp ─────────────────────────────────────────────────
        self._draw_separator(x, y, UI_PANEL_WIDTH - UI_MARGIN * 2)
        y += 8
        y += self._draw_text("── Time Warp ──", x, y, (120, 130, 160))
        y += 4
        # Draw tier indicators as a horizontal bar
        tier_x = x
        for i, tier in enumerate(TIME_WARP_TIERS):
            label = f"x{int(tier)}"
            if i == time_warp_index:
                # Active tier: bright cyan
                warp_color = (80, 255, 220)
                prefix = "►"
            else:
                warp_color = (70, 70, 90)
                prefix = " "
            y += self._draw_text(f" {prefix} {label}", tier_x, y, warp_color,
                                 self.small_font)
        y += 4
        y += self._draw_text("W → cycle warp tier", x, y, (100, 100, 120),
                             self.small_font)
        y += 8

        # ── Spawn Type ────────────────────────────────────────────────
        self._draw_separator(x, y, UI_PANEL_WIDTH - UI_MARGIN * 2)
        y += 8
        y += self._draw_text("── Spawn Type ──", x, y, (120, 130, 160))
        y += 4
        y += self._draw_text(f"Type: {current_type}", x, y, UI_HIGHLIGHT_COLOR)
        y += self._draw_text("T → cycle type", x, y, (100, 100, 120))
        y += 8

        # ── Selected Body ─────────────────────────────────────────────
        self._draw_separator(x, y, UI_PANEL_WIDTH - UI_MARGIN * 2)
        y += 8
        y += self._draw_text("── Selected Body ──", x, y, (120, 130, 160))
        y += 4

        if selected_body is not None:
            b = selected_body
            y += self._draw_text(f"ID:      #{b.id}", x, y)
            y += self._draw_text(f"Type:    {b.body_type}", x, y)
            y += self._draw_text(f"Mass:    {format_number(b.mass)}", x, y)
            speed = b.speed()
            y += self._draw_text(f"Speed:   {format_number(speed)}", x, y)
            dist_com = vec_distance(b.position, physics_engine.center_of_mass)
            y += self._draw_text(f"Dist COM:{format_number(dist_com)}", x, y)
            y += self._draw_text(
                f"Pos:     ({format_number(b.position[0])}, "
                f"{format_number(b.position[1])})", x, y,
            )
        else:
            y += self._draw_text("(none)", x, y, (100, 100, 120))
        y += 8

        # ── Controls ──────────────────────────────────────────────────
        self._draw_separator(x, y, UI_PANEL_WIDTH - UI_MARGIN * 2)
        y += 8
        y += self._draw_text("── Controls ──", x, y, (120, 130, 160))
        y += 4

        controls = [
            "LMB       spawn / select",
            "Drag      set velocity",
            "MMB       pan camera",
            "Scroll    zoom",
            "SPACE     pause / resume",
            "R         reset",
            "C         clear trails",
            "UP/DOWN   speed",
            "W         time warp",
            "T         cycle type",
            "F         follow selected",
            "G         follow COM",
            "D         debug mode",
            "1-5       load preset",
            "DEL       delete selected",
        ]
        for line in controls:
            y += self._draw_text(line, x, y, (90, 95, 115), self.small_font)
