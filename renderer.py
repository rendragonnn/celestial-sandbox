"""
renderer.py – Rendering engine for the Celestial Sandbox.

Responsible for drawing the starfield background, celestial bodies with
enhanced glow shader effects and procedural textures, orbit trails,
velocity vectors, mini map, and the center-of-mass marker.
All drawing goes through the Camera for coordinate mapping.
"""

import pygame
import math
import random

from config import (
    WINDOW_WIDTH, WINDOW_HEIGHT, BG_COLOR, STAR_COUNT, STAR_LAYER_COUNT,
    COLOR_WHITE, COLOR_CYAN, COLOR_YELLOW,
    GLOW_LAYERS, GLOW_ALPHA_BASE, GLOW_INNER_ALPHA,
    GLOW_OUTER_RADIUS_FACTOR, GLOW_INNER_RADIUS_FACTOR,
    VELOCITY_ARROW_COLOR, VELOCITY_ARROW_SCALE,
    MINIMAP_WIDTH, MINIMAP_HEIGHT, MINIMAP_MARGIN,
    MINIMAP_BG_ALPHA, MINIMAP_BG_COLOR, MINIMAP_BORDER_COLOR,
    MINIMAP_BODY_MIN_SIZE, MINIMAP_VIEW_COLOR,
)
from vector_math import vec_add, vec_sub, vec_scale, vec_magnitude, vec_normalize
from utils import dim_color, lerp_color, brighten_color


class Renderer:
    """
    Handles all visual output: background, bodies, trails, HUD overlays.
    """

    def __init__(self, surface, camera):
        self.surface = surface
        self.camera = camera
        self.stars = self._generate_starfield()
        # Cache for procedural body textures: body_id → Surface
        self._texture_cache = {}

    # ── Starfield ─────────────────────────────────────────────────────────

    def _generate_starfield(self):
        """
        Create a procedural multi-layer starfield.

        Returns a list of (x, y, radius, brightness, layer) tuples.
        """
        stars = []
        for _ in range(STAR_COUNT):
            x = random.randint(0, WINDOW_WIDTH)
            y = random.randint(0, WINDOW_HEIGHT)
            layer = random.randint(1, STAR_LAYER_COUNT)
            radius = random.choice([1, 1, 1, 2]) if layer < 3 else 1
            brightness = random.randint(80, 230)
            stars.append((x, y, radius, brightness, layer))
        return stars

    def draw_starfield(self):
        """Render the static starfield behind everything else."""
        for x, y, r, brightness, layer in self.stars:
            # Slight parallax: deeper layers shift less with camera
            factor = 0.02 * layer
            sx = int((x - self.camera.offset[0] * factor) % WINDOW_WIDTH)
            sy = int((y - self.camera.offset[1] * factor) % WINDOW_HEIGHT)
            color = (brightness, brightness, min(255, brightness + 20))
            if r == 1:
                self.surface.set_at((sx, sy), color)
            else:
                pygame.draw.circle(self.surface, color, (sx, sy), r)

    # ── Procedural Textures ───────────────────────────────────────────────

    def _get_texture(self, body, screen_radius):
        """
        Return a cached procedural texture Surface for the given body.
        Regenerates if the body was never seen or its rendered size changed
        significantly.
        """
        sr = max(4, int(screen_radius))
        cache_key = body.id
        # Check cache: reuse if radius hasn't changed much
        if cache_key in self._texture_cache:
            cached_sr, cached_surf = self._texture_cache[cache_key]
            if abs(cached_sr - sr) < 3:
                return cached_surf

        size = sr * 2
        surf = pygame.Surface((size, size), pygame.SRCALPHA)

        if body.body_type == "Gas Giant":
            self._draw_gas_giant_texture(surf, sr, body.color)
        elif body.body_type in ("Planet", "Dwarf Planet"):
            self._draw_rocky_texture(surf, sr, body.color)
        elif body.body_type == "Star":
            self._draw_star_texture(surf, sr, body.color)
        else:
            # Black hole or fallback: solid circle
            pygame.draw.circle(surf, body.color, (sr, sr), sr)

        self._texture_cache[cache_key] = (sr, surf)
        return surf

    @staticmethod
    def _draw_gas_giant_texture(surf, sr, base_color):
        """
        Draw horizontal banding stripes for a gas giant.
        Alternates between the base color and a lighter/darker variant.
        """
        cx, cy = sr, sr
        # Draw base circle
        pygame.draw.circle(surf, base_color, (cx, cy), sr)

        # Draw horizontal bands
        band_count = max(3, sr // 3)
        band_height = max(1, (sr * 2) // band_count)
        r, g, b = base_color

        for i in range(band_count):
            y_top = i * band_height
            # Alternate lighter and darker bands
            if i % 2 == 0:
                band_color = (min(255, r + 30), min(255, g + 20), min(255, b + 10), 60)
            else:
                band_color = (max(0, r - 25), max(0, g - 20), max(0, b - 15), 50)

            # Create a band rect clipped to the circle
            band_surf = pygame.Surface((sr * 2, band_height), pygame.SRCALPHA)
            band_surf.fill(band_color)
            surf.blit(band_surf, (0, y_top))

        # Re-mask to circle shape (clear pixels outside the circle)
        mask_surf = pygame.Surface((sr * 2, sr * 2), pygame.SRCALPHA)
        pygame.draw.circle(mask_surf, (255, 255, 255, 255), (cx, cy), sr)
        # Apply mask: keep only pixels inside the circle
        final = pygame.Surface((sr * 2, sr * 2), pygame.SRCALPHA)
        final.blit(surf, (0, 0))
        final.blit(mask_surf, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
        surf.fill((0, 0, 0, 0))
        surf.blit(final, (0, 0))

        # Subtle gradient overlay for 3D look (lighter top-left)
        highlight = pygame.Surface((sr * 2, sr * 2), pygame.SRCALPHA)
        pygame.draw.circle(
            highlight, (255, 255, 255, 25),
            (cx - sr // 4, cy - sr // 4), sr // 2,
        )
        surf.blit(highlight, (0, 0))

    @staticmethod
    def _draw_rocky_texture(surf, sr, base_color):
        """
        Draw a rocky surface texture with darker splotches and a specular
        highlight for a 3D effect.
        """
        cx, cy = sr, sr
        pygame.draw.circle(surf, base_color, (cx, cy), sr)

        # Random darker spots (craters / terrain)
        rng = random.Random(hash(base_color) & 0xFFFFFFFF)
        num_spots = max(2, sr // 2)
        for _ in range(num_spots):
            angle = rng.uniform(0, math.pi * 2)
            dist = rng.uniform(0, sr * 0.7)
            sx = int(cx + math.cos(angle) * dist)
            sy = int(cy + math.sin(angle) * dist)
            spot_r = max(1, rng.randint(1, max(1, sr // 4)))
            r, g, b = base_color
            dark = (max(0, r - 40), max(0, g - 40), max(0, b - 30), 80)
            pygame.draw.circle(surf, dark, (sx, sy), spot_r)

        # Specular highlight (top-left shine)
        highlight = pygame.Surface((sr * 2, sr * 2), pygame.SRCALPHA)
        hl_radius = max(2, sr // 3)
        pygame.draw.circle(
            highlight, (255, 255, 255, 40),
            (cx - sr // 4, cy - sr // 4), hl_radius,
        )
        surf.blit(highlight, (0, 0))

    @staticmethod
    def _draw_star_texture(surf, sr, base_color):
        """
        Draw a star with a radial gradient from bright center to body color.
        """
        cx, cy = sr, sr
        # Radial gradient: concentric circles from bright center to edge
        steps = max(3, sr)
        r, g, b = base_color
        for i in range(steps, 0, -1):
            t = i / steps
            cr = int(min(255, r + (255 - r) * (1 - t) * 0.8))
            cg = int(min(255, g + (255 - g) * (1 - t) * 0.6))
            cb = int(min(255, b + (255 - b) * (1 - t) * 0.4))
            radius = int(sr * t)
            if radius > 0:
                pygame.draw.circle(surf, (cr, cg, cb), (cx, cy), radius)

    # ── Bodies ────────────────────────────────────────────────────────────

    def draw_body(self, body):
        """
        Draw a single celestial body with enhanced multi-layer glow
        (outer + inner), procedural texture, and selection highlight.
        """
        screen_pos = self.camera.world_to_screen(body.position)
        screen_radius = self.camera.world_radius_to_screen(body.radius)
        ix, iy = int(screen_pos[0]), int(screen_pos[1])

        # Cull: skip bodies far off-screen
        margin = screen_radius + 80
        if (ix < -margin or ix > WINDOW_WIDTH + margin or
                iy < -margin or iy > WINDOW_HEIGHT + margin):
            return

        # ── Outer Glow (wide, soft, color-tinted) ─────────────────────
        outer_extent = int(screen_radius + GLOW_LAYERS * GLOW_OUTER_RADIUS_FACTOR)
        glow_surf_size = int(outer_extent * 2 + 4)
        if glow_surf_size < 4:
            glow_surf_size = 4
        glow_surf = pygame.Surface((glow_surf_size, glow_surf_size), pygame.SRCALPHA)
        center = (glow_surf_size // 2, glow_surf_size // 2)

        for i in range(GLOW_LAYERS, 0, -1):
            t = i / GLOW_LAYERS  # 1.0 = outermost, 0.0 = innermost
            alpha = max(3, int(GLOW_ALPHA_BASE * (1 - t * 0.6)))
            r = int(screen_radius + i * GLOW_OUTER_RADIUS_FACTOR)
            # Color shifts from body glow_color (inner) toward a dimmer version (outer)
            gc = body.glow_color
            glow_color = (
                max(0, int(gc[0] * (0.5 + 0.5 * (1 - t)))),
                max(0, int(gc[1] * (0.5 + 0.5 * (1 - t)))),
                max(0, int(gc[2] * (0.5 + 0.5 * (1 - t)))),
                alpha,
            )
            pygame.draw.circle(glow_surf, glow_color, center, r)

        self.surface.blit(
            glow_surf,
            (ix - glow_surf_size // 2, iy - glow_surf_size // 2),
        )

        # ── Inner Glow (bright core halo) ─────────────────────────────
        inner_r = max(2, int(screen_radius * GLOW_INNER_RADIUS_FACTOR))
        inner_surf_size = int(screen_radius * 2.4 + 4)
        inner_surf = pygame.Surface((inner_surf_size, inner_surf_size), pygame.SRCALPHA)
        ic = (inner_surf_size // 2, inner_surf_size // 2)
        # Bright white-ish inner halo
        for step in range(3, 0, -1):
            a = max(10, GLOW_INNER_ALPHA // step)
            rr = inner_r + step * 2
            bright = brighten_color(body.color, 1.6)
            pygame.draw.circle(inner_surf, (*bright, a), ic, rr)
        self.surface.blit(
            inner_surf,
            (ix - inner_surf_size // 2, iy - inner_surf_size // 2),
        )

        # ── Body texture (procedural) ─────────────────────────────────
        if screen_radius >= 3:
            tex = self._get_texture(body, screen_radius)
            tw, th = tex.get_size()
            self.surface.blit(tex, (ix - tw // 2, iy - th // 2))
        elif screen_radius >= 1:
            pygame.draw.circle(self.surface, body.color, (ix, iy), int(screen_radius))

        # ── Black hole special rendering ──────────────────────────────
        if body.body_type == "Black Hole":
            # Dark core
            core_r = max(1, int(screen_radius * 0.65))
            pygame.draw.circle(self.surface, (3, 0, 8), (ix, iy), core_r)
            # Event horizon ring
            eh_r = max(2, int(screen_radius * 1.1))
            pygame.draw.circle(self.surface, (100, 50, 160), (ix, iy), eh_r, 1)
            # Accretion disk glow
            for ring_i in range(3):
                ring_r = int(screen_radius * (1.4 + ring_i * 0.25))
                ring_alpha = max(15, 70 - ring_i * 20)
                ring_surf = pygame.Surface(
                    (ring_r * 2 + 4, ring_r * 2 + 4), pygame.SRCALPHA
                )
                ring_color = (180 - ring_i * 30, 80 + ring_i * 10, 255, ring_alpha)
                pygame.draw.circle(
                    ring_surf, ring_color,
                    (ring_r + 2, ring_r + 2), ring_r, 2
                )
                self.surface.blit(ring_surf, (ix - ring_r - 2, iy - ring_r - 2))

        # ── Selection highlight ───────────────────────────────────────
        if body.is_selected:
            sel_radius = int(screen_radius + 8)
            # Pulsing selection ring
            pygame.draw.circle(self.surface, COLOR_CYAN, (ix, iy), sel_radius, 2)
            pygame.draw.circle(self.surface, (*COLOR_CYAN, 60), (ix, iy), sel_radius + 4, 1)

    # ── Orbit Trails ──────────────────────────────────────────────────────

    def draw_trail(self, body):
        """
        Draw a fading orbit trail for a body.
        """
        trail = body.trail
        n = len(trail)
        if n < 2:
            return

        fade_color = dim_color(body.color, 0.6)

        for i in range(1, n):
            # Fade: older segments are more transparent
            t = i / n
            color = lerp_color((20, 20, 40), fade_color, t)

            p1 = self.camera.world_to_screen(trail[i - 1])
            p2 = self.camera.world_to_screen(trail[i])

            # Cull off-screen segments
            if (min(p1[0], p2[0]) > WINDOW_WIDTH + 50 or
                    max(p1[0], p2[0]) < -50 or
                    min(p1[1], p2[1]) > WINDOW_HEIGHT + 50 or
                    max(p1[1], p2[1]) < -50):
                continue

            pygame.draw.line(
                self.surface, color,
                (int(p1[0]), int(p1[1])),
                (int(p2[0]), int(p2[1])),
                1,
            )

    # ── Velocity Arrow ────────────────────────────────────────────────────

    def draw_velocity_arrow(self, start_world, end_world):
        """
        Draw a velocity-vector arrow from start to end in world space.
        Used during mouse-drag body creation.
        """
        s1 = self.camera.world_to_screen(start_world)
        s2 = self.camera.world_to_screen(end_world)
        pygame.draw.line(
            self.surface, VELOCITY_ARROW_COLOR,
            (int(s1[0]), int(s1[1])),
            (int(s2[0]), int(s2[1])),
            2,
        )
        # Arrowhead
        direction = vec_sub(s2, s1)
        length = vec_magnitude(direction)
        if length > 10:
            d = vec_normalize(direction)
            perp = (-d[1], d[0])
            tip = s2
            left = vec_sub(tip, vec_add(vec_scale(d, 10), vec_scale(perp, 5)))
            right = vec_sub(tip, vec_sub(vec_scale(d, 10), vec_scale(perp, 5)))
            pygame.draw.polygon(
                self.surface, VELOCITY_ARROW_COLOR,
                [(int(tip[0]), int(tip[1])),
                 (int(left[0]), int(left[1])),
                 (int(right[0]), int(right[1]))],
            )

    # ── Center of Mass Marker ─────────────────────────────────────────────

    def draw_com_marker(self, com_world):
        """Draw a small cross at the system center of mass."""
        sp = self.camera.world_to_screen(com_world)
        ix, iy = int(sp[0]), int(sp[1])
        size = 8
        color = COLOR_YELLOW
        pygame.draw.line(self.surface, color, (ix - size, iy), (ix + size, iy), 1)
        pygame.draw.line(self.surface, color, (ix, iy - size), (ix, iy + size), 1)

    # ── Mini Map ──────────────────────────────────────────────────────────

    def draw_minimap(self, physics_engine):
        """
        Draw a mini overview map in the bottom-left corner showing all
        bodies and the current camera viewport rectangle.
        """
        bodies = physics_engine.bodies
        if not bodies:
            return

        # Determine world bounding box of all bodies
        min_x = min(b.position[0] for b in bodies)
        max_x = max(b.position[0] for b in bodies)
        min_y = min(b.position[1] for b in bodies)
        max_y = max(b.position[1] for b in bodies)

        # Add some padding
        pad = 100
        min_x -= pad
        max_x += pad
        min_y -= pad
        max_y += pad

        world_w = max(max_x - min_x, 1)
        world_h = max(max_y - min_y, 1)

        # Position: bottom-left
        map_x = MINIMAP_MARGIN
        map_y = WINDOW_HEIGHT - MINIMAP_HEIGHT - MINIMAP_MARGIN

        # Background surface
        map_surf = pygame.Surface(
            (MINIMAP_WIDTH, MINIMAP_HEIGHT), pygame.SRCALPHA
        )
        map_surf.fill((*MINIMAP_BG_COLOR, MINIMAP_BG_ALPHA))

        # Scale factors
        scale_x = (MINIMAP_WIDTH - 8) / world_w
        scale_y = (MINIMAP_HEIGHT - 8) / world_h
        scale = min(scale_x, scale_y)

        # Offset to center the content in the minimap
        content_w = world_w * scale
        content_h = world_h * scale
        off_x = (MINIMAP_WIDTH - content_w) / 2
        off_y = (MINIMAP_HEIGHT - content_h) / 2

        def world_to_map(wx, wy):
            mx = off_x + (wx - min_x) * scale
            my = off_y + (wy - min_y) * scale
            return (int(mx), int(my))

        # Draw bodies as dots
        for b in bodies:
            mx, my = world_to_map(b.position[0], b.position[1])
            dot_r = max(MINIMAP_BODY_MIN_SIZE, int(b.radius * scale * 0.5))
            dot_r = min(dot_r, 6)  # cap size
            pygame.draw.circle(map_surf, b.color, (mx, my), dot_r)

        # Draw camera viewport rectangle
        cam = self.camera
        # Get world-space corners of the screen
        tl = cam.screen_to_world((0, 0))
        br = cam.screen_to_world((WINDOW_WIDTH, WINDOW_HEIGHT))
        vp_x1, vp_y1 = world_to_map(tl[0], tl[1])
        vp_x2, vp_y2 = world_to_map(br[0], br[1])
        vp_w = max(1, vp_x2 - vp_x1)
        vp_h = max(1, vp_y2 - vp_y1)
        # Clamp viewport rect to minimap bounds
        vp_rect = pygame.Rect(vp_x1, vp_y1, vp_w, vp_h)
        vp_rect.clamp_ip(pygame.Rect(0, 0, MINIMAP_WIDTH, MINIMAP_HEIGHT))
        pygame.draw.rect(map_surf, MINIMAP_VIEW_COLOR, vp_rect, 1)

        # Border
        pygame.draw.rect(
            map_surf, MINIMAP_BORDER_COLOR,
            (0, 0, MINIMAP_WIDTH, MINIMAP_HEIGHT), 1,
        )

        # Label
        try:
            font = pygame.font.SysFont("Consolas", 11)
            label = font.render("MINI MAP", True, (100, 120, 160))
            map_surf.blit(label, (4, 2))
        except Exception:
            pass

        self.surface.blit(map_surf, (map_x, map_y))

    # ── Full Frame ────────────────────────────────────────────────────────

    def render_frame(self, physics_engine, show_trails=True, show_velocity=True,
                     drag_state=None):
        """
        Draw a complete frame:
            1. Clear to background
            2. Starfield
            3. Orbit trails
            4. Bodies
            5. Center-of-mass marker
            6. Drag velocity arrow (if applicable)
            7. Mini map
        """
        # 1. Background
        self.surface.fill(BG_COLOR)

        # 2. Starfield
        self.draw_starfield()

        # 3. Trails
        if show_trails:
            for body in physics_engine.bodies:
                self.draw_trail(body)

        # 4. Bodies
        for body in physics_engine.bodies:
            self.draw_body(body)

        # 5. COM marker
        if physics_engine.bodies:
            self.draw_com_marker(physics_engine.center_of_mass)

        # 6. Drag arrow
        if drag_state is not None:
            start, end = drag_state
            self.draw_velocity_arrow(start, end)

        # 7. Mini map
        self.draw_minimap(physics_engine)
