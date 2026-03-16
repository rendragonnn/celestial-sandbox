"""
utils.py – Utility helpers for the Celestial Sandbox.

Provides ID generation, color manipulation, and miscellaneous helpers.
"""

import random
import math


# ─── Unique ID Generator ─────────────────────────────────────────────────────

_next_id = 0

def generate_id():
    """Return a unique integer ID for a new body."""
    global _next_id
    _next_id += 1
    return _next_id


def reset_id_counter():
    """Reset the ID counter (useful when resetting the simulation)."""
    global _next_id
    _next_id = 0


# ─── Color Utilities ─────────────────────────────────────────────────────────

def brighten_color(color, factor=1.3):
    """Return a brightened version of an RGB tuple."""
    return tuple(min(255, int(c * factor)) for c in color)


def dim_color(color, factor=0.5):
    """Return a dimmed version of an RGB tuple."""
    return tuple(max(0, int(c * factor)) for c in color)


def lerp_color(c1, c2, t):
    """Linearly interpolate between two RGB colors by factor t ∈ [0, 1]."""
    return tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))


def random_color():
    """Generate a random visually pleasant RGB color."""
    h = random.uniform(0, 1)
    s = random.uniform(0.5, 1.0)
    v = random.uniform(0.7, 1.0)
    return hsv_to_rgb(h, s, v)


def hsv_to_rgb(h, s, v):
    """Convert HSV (each in 0-1) to an RGB tuple (0-255)."""
    i = int(h * 6.0)
    f = h * 6.0 - i
    p = v * (1.0 - s)
    q = v * (1.0 - f * s)
    t = v * (1.0 - (1.0 - f) * s)
    i %= 6
    if i == 0:
        r, g, b = v, t, p
    elif i == 1:
        r, g, b = q, v, p
    elif i == 2:
        r, g, b = p, v, t
    elif i == 3:
        r, g, b = p, q, v
    elif i == 4:
        r, g, b = t, p, v
    else:
        r, g, b = v, p, q
    return (int(r * 255), int(g * 255), int(b * 255))


# ─── Misc ─────────────────────────────────────────────────────────────────────

def clamp(value, lo, hi):
    """Clamp a value between lo and hi."""
    return max(lo, min(hi, value))


def format_number(n):
    """Format a number for display (use scientific notation if large)."""
    if abs(n) >= 1e6:
        return f"{n:.2e}"
    if abs(n) >= 1000:
        return f"{n:,.0f}"
    if abs(n) >= 1:
        return f"{n:.1f}"
    return f"{n:.3f}"
