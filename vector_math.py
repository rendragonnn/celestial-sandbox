"""
vector_math.py – Lightweight 2D vector math utilities.

All vectors are represented as (x, y) tuples for simplicity and speed.
These pure-function helpers avoid external dependencies.
"""

import math


def vec_add(a, b):
    """Return the sum of two vectors."""
    return (a[0] + b[0], a[1] + b[1])


def vec_sub(a, b):
    """Return the difference a - b."""
    return (a[0] - b[0], a[1] - b[1])


def vec_scale(v, scalar):
    """Scale a vector by a scalar."""
    return (v[0] * scalar, v[1] * scalar)


def vec_magnitude(v):
    """Return the magnitude (length) of a vector."""
    return math.sqrt(v[0] * v[0] + v[1] * v[1])


def vec_normalize(v):
    """Return the unit vector. Returns (0, 0) for zero-length vectors."""
    mag = vec_magnitude(v)
    if mag == 0:
        return (0.0, 0.0)
    return (v[0] / mag, v[1] / mag)


def vec_distance(a, b):
    """Return the Euclidean distance between two points."""
    dx = b[0] - a[0]
    dy = b[1] - a[1]
    return math.sqrt(dx * dx + dy * dy)


def vec_distance_sq(a, b):
    """Return the squared distance (avoids sqrt for comparisons)."""
    dx = b[0] - a[0]
    dy = b[1] - a[1]
    return dx * dx + dy * dy


def vec_dot(a, b):
    """Return the dot product of two vectors."""
    return a[0] * b[0] + a[1] * b[1]


def vec_angle(v):
    """Return the angle of the vector in radians."""
    return math.atan2(v[1], v[0])


def vec_from_angle(angle, length=1.0):
    """Create a vector from an angle (radians) and optional length."""
    return (math.cos(angle) * length, math.sin(angle) * length)


def vec_lerp(a, b, t):
    """Linearly interpolate between two vectors by factor t ∈ [0, 1]."""
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)


def vec_negate(v):
    """Return the negated vector."""
    return (-v[0], -v[1])


def vec_rotate(v, angle):
    """Rotate a vector by the given angle (radians)."""
    cos_a = math.cos(angle)
    sin_a = math.sin(angle)
    return (v[0] * cos_a - v[1] * sin_a, v[0] * sin_a + v[1] * cos_a)
