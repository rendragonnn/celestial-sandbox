"""
main.py – Entry point for the Celestial Sandbox simulation.

Manages the Pygame event loop, user input, and coordinates between the
physics engine, renderer, camera, UI panel, and debug tools.
"""

import sys
import pygame
import asyncio

from config import (
    WINDOW_WIDTH, WINDOW_HEIGHT, FPS, TITLE, DT_BASE,
    SPEED_MIN, SPEED_MAX, SPEED_STEP, VELOCITY_ARROW_SCALE,
    BODY_TYPES, DEFAULT_BODY_TYPE, UI_PANEL_WIDTH,
    TIME_WARP_TIERS,
)
from physics_engine import PhysicsEngine
from renderer import Renderer
from camera import Camera
from ui_panel import UIPanel
from debug_tools import DebugTools
from body import CelestialBody
from preset_systems import PRESETS
from utils import reset_id_counter


# ─── Body type cycle order ────────────────────────────────────────────────────
BODY_TYPE_CYCLE = ["Planet", "Gas Giant", "Dwarf Planet", "Star", "Black Hole"]


class Simulation:
    """
    Top-level simulation controller.

    Responsibilities:
        • Initialize Pygame and all subsystems
        • Process user input (keyboard + mouse)
        • Orchestrate the physics → camera → render pipeline
        • Manage simulation state (pause, speed, selected body, etc.)
    """

    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption(TITLE)
        self.clock = pygame.time.Clock()

        # Subsystems
        self.camera = Camera()
        self.physics = PhysicsEngine()
        self.renderer = Renderer(self.screen, self.camera)
        self.ui_panel = UIPanel(self.screen)
        self.debug = DebugTools(self.screen, self.camera)

        # Simulation state
        self.running = True
        self.paused = False
        self.sim_speed = 1.0
        self.show_trails = True
        self.selected_body = None

        # Time warp mode
        self.time_warp_index = 0
        self.time_warp = TIME_WARP_TIERS[0]

        # Spawn control
        self.current_type_index = 0
        self.current_type = BODY_TYPE_CYCLE[self.current_type_index]

        # Mouse drag state for velocity definition
        self._dragging = False
        self._drag_start_world = None
        self._drag_start_screen = None
        self._drag_body_preview = None   # position where the body will spawn

        # Notification overlay (brief flash messages)
        self._notification = None
        self._notification_timer = 0

        # Load the solar system preset by default
        self._load_preset(2)

    # ── Main Loop ─────────────────────────────────────────────────────────

    async def run(self):
        """Main game loop."""
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0  # seconds since last frame

            self._handle_events()
            self._update(dt)
            self._draw()

            pygame.display.flip()
            await asyncio.sleep(0)  # Required for Pygbag browser rendering

        pygame.quit()
        sys.exit()

    # ── Input Handling ────────────────────────────────────────────────────

    def _handle_events(self):
        """Process all Pygame events for the current frame."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            # ── Keyboard ──────────────────────────────────────────────
            elif event.type == pygame.KEYDOWN:
                self._handle_key_down(event.key)

            # ── Mouse Button Down ─────────────────────────────────────
            elif event.type == pygame.MOUSEBUTTONDOWN:
                self._handle_mouse_down(event)

            # ── Mouse Button Up ───────────────────────────────────────
            elif event.type == pygame.MOUSEBUTTONUP:
                self._handle_mouse_up(event)

            # ── Mouse Motion ──────────────────────────────────────────
            elif event.type == pygame.MOUSEMOTION:
                self._handle_mouse_motion(event)

            # ── Mouse Wheel (zoom) ────────────────────────────────────
            elif event.type == pygame.MOUSEWHEEL:
                mouse_pos = pygame.mouse.get_pos()
                if event.y > 0:
                    self.camera.zoom_at(mouse_pos, zoom_in=True)
                elif event.y < 0:
                    self.camera.zoom_at(mouse_pos, zoom_in=False)

    def _handle_key_down(self, key):
        """Handle a single key-down event."""
        if key == pygame.K_SPACE:
            self.paused = not self.paused
            self._notify("PAUSED" if self.paused else "RUNNING")

        elif key == pygame.K_r:
            self._reset()
            self._notify("Simulation Reset")

        elif key == pygame.K_c:
            for b in self.physics.bodies:
                b.clear_trail()
            self._notify("Trails Cleared")

        elif key == pygame.K_UP:
            self.sim_speed = min(SPEED_MAX, self.sim_speed + SPEED_STEP)
            self._notify(f"Speed: {self.sim_speed:.1f}x")

        elif key == pygame.K_DOWN:
            self.sim_speed = max(SPEED_MIN, self.sim_speed - SPEED_STEP)
            self._notify(f"Speed: {self.sim_speed:.1f}x")

        elif key == pygame.K_d:
            self.debug.toggle()
            self._notify("Debug " + ("ON" if self.debug.enabled else "OFF"))

        elif key == pygame.K_t:
            self.current_type_index = (
                (self.current_type_index + 1) % len(BODY_TYPE_CYCLE)
            )
            self.current_type = BODY_TYPE_CYCLE[self.current_type_index]
            self._notify(f"Spawn: {self.current_type}")

        elif key == pygame.K_f:
            if self.selected_body is not None:
                self.camera.set_follow_body(self.selected_body)
                self._notify(f"Following Body #{self.selected_body.id}")
            else:
                self.camera.stop_following()

        elif key == pygame.K_g:
            self.camera.set_follow_com()
            self._notify("Following Center of Mass")

        elif key == pygame.K_w:
            self.time_warp_index = (
                (self.time_warp_index + 1) % len(TIME_WARP_TIERS)
            )
            self.time_warp = TIME_WARP_TIERS[self.time_warp_index]
            self._notify(f"Time Warp: x{int(self.time_warp)}")

        elif key == pygame.K_DELETE:
            if self.selected_body is not None:
                self.physics.remove_body(self.selected_body)
                self._notify(f"Deleted Body #{self.selected_body.id}")
                self.selected_body = None

        # Preset keys 1–5
        elif key in (pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4, pygame.K_5):
            preset_num = key - pygame.K_0
            self._load_preset(preset_num)

    def _handle_mouse_down(self, event):
        """Handle mouse button press."""
        # Middle click → start camera pan
        if event.button == 2:
            self.camera.start_pan(event.pos)
            return

        # Left click
        if event.button == 1:
            # Ignore clicks on the UI panel area
            if event.pos[0] > WINDOW_WIDTH - UI_PANEL_WIDTH:
                return

            world_pos = self.camera.screen_to_world(event.pos)

            # Check if we clicked on an existing body
            clicked_body = self.physics.get_body_at(
                world_pos, threshold=20 / self.camera.zoom
            )

            if clicked_body is not None:
                # Select the body
                self._select_body(clicked_body)
            else:
                # Start drag-to-spawn
                self._dragging = True
                self._drag_start_world = world_pos
                self._drag_start_screen = event.pos

    def _handle_mouse_up(self, event):
        """Handle mouse button release."""
        # Middle click → end pan
        if event.button == 2:
            self.camera.end_pan()
            return

        # Left click release → finish drag-to-spawn
        if event.button == 1 and self._dragging:
            self._dragging = False
            world_pos = self.camera.screen_to_world(event.pos)

            # Velocity = direction from release to start (body launches away)
            vx = (self._drag_start_world[0] - world_pos[0]) * VELOCITY_ARROW_SCALE
            vy = (self._drag_start_world[1] - world_pos[1]) * VELOCITY_ARROW_SCALE

            body = CelestialBody(
                self._drag_start_world[0],
                self._drag_start_world[1],
                vx, vy,
                body_type=self.current_type,
            )
            self.physics.add_body(body)
            self._select_body(body)

    def _handle_mouse_motion(self, event):
        """Handle mouse movement."""
        # Camera panning
        if pygame.mouse.get_pressed()[1]:  # middle button held
            self.camera.update_pan(event.pos)

    # ── Utility ───────────────────────────────────────────────────────────

    def _select_body(self, body):
        """Select a body for inspection."""
        # Deselect previous
        if self.selected_body is not None:
            self.selected_body.is_selected = False
        self.selected_body = body
        body.is_selected = True

    def _load_preset(self, number):
        """Load a preset by number (1–5)."""
        if number not in PRESETS:
            return
        name, factory = PRESETS[number]
        self._reset()
        bodies = factory()
        for b in bodies:
            self.physics.add_body(b)
        self._notify(f"Loaded: {name}")

    def _reset(self):
        """Reset the entire simulation."""
        self.physics.clear()
        self.selected_body = None
        self.camera.reset()
        self.paused = False
        self.sim_speed = 1.0
        self.time_warp_index = 0
        self.time_warp = TIME_WARP_TIERS[0]
        reset_id_counter()

    def _notify(self, msg):
        """Show a brief notification message on screen."""
        self._notification = msg
        self._notification_timer = 90  # frames

    # ── Update ────────────────────────────────────────────────────────────

    def _update(self, dt):
        """Advance simulation state by one frame."""
        # Physics
        if not self.paused:
            physics_dt = DT_BASE * self.sim_speed * self.time_warp
            self.physics.step(physics_dt)

        # Camera
        self.camera.update(self.physics.center_of_mass)

        # Check if selected body is still alive
        if (self.selected_body is not None and
                self.selected_body not in self.physics.bodies):
            self.selected_body = None

        # Notification countdown
        if self._notification_timer > 0:
            self._notification_timer -= 1

    # ── Drawing ───────────────────────────────────────────────────────────

    def _draw(self):
        """Render the complete frame."""
        # Prepare drag state for renderer
        drag_state = None
        if self._dragging and self._drag_start_world is not None:
            mouse_screen = pygame.mouse.get_pos()
            mouse_world = self.camera.screen_to_world(mouse_screen)
            drag_state = (self._drag_start_world, mouse_world)

        # Render scene
        self.renderer.render_frame(
            self.physics,
            show_trails=self.show_trails,
            drag_state=drag_state,
        )

        # Debug overlay
        self.debug.draw(self.physics, self.clock, self.sim_speed)

        # UI Panel
        self.ui_panel.draw(
            self.physics,
            self.sim_speed,
            self.paused,
            self.selected_body,
            self.current_type,
            self.time_warp_index,
        )

        # Notification overlay
        self._draw_notification()

    def _draw_notification(self):
        """Draw the brief flash notification (top-center)."""
        if self._notification_timer <= 0 or self._notification is None:
            return
        alpha = min(255, self._notification_timer * 6)
        font = pygame.font.SysFont("Consolas", 22, bold=True)
        text_surf = font.render(self._notification, True, (255, 255, 255))
        text_rect = text_surf.get_rect(
            center=(
                (WINDOW_WIDTH - UI_PANEL_WIDTH) // 2,
                40,
            )
        )
        # Background pill
        bg_rect = text_rect.inflate(24, 12)
        bg_surf = pygame.Surface((bg_rect.width, bg_rect.height), pygame.SRCALPHA)
        bg_surf.fill((20, 20, 40, min(180, alpha)))
        pygame.draw.rect(
            bg_surf, (80, 200, 255, min(120, alpha)),
            bg_surf.get_rect(), 1, border_radius=8,
        )
        self.screen.blit(bg_surf, bg_rect.topleft)
        text_surf.set_alpha(alpha)
        self.screen.blit(text_surf, text_rect)


# ─── Entry Point ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    sim = Simulation()
    asyncio.run(sim.run())
