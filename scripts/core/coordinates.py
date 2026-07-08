"""Normalized (0–1000) ↔ viewport pixel coordinate mapping for G1 grounding."""

from __future__ import annotations

NORM_MAX = 1000
COORDINATE_SPACE = "norm_1000"


def norm_to_pixel(coord_norm: int, viewport_size: int) -> int:
    """Map a normalized coordinate to a viewport pixel index."""
    if viewport_size <= 1:
        return 0
    bounded = max(0, min(coord_norm, NORM_MAX))
    return round(bounded / NORM_MAX * (viewport_size - 1))


def pixel_to_norm(coord_px: int, viewport_size: int) -> int:
    """Map a viewport pixel index to normalized coordinates."""
    if viewport_size <= 1:
        return 0
    max_px = viewport_size - 1
    bounded = max(0, min(coord_px, max_px))
    return round(bounded / max_px * NORM_MAX)


def norm_coords_to_pixels(
    x_norm: int,
    y_norm: int,
    viewport_width: int,
    viewport_height: int,
) -> tuple[int, int]:
    return (
        norm_to_pixel(x_norm, viewport_width),
        norm_to_pixel(y_norm, viewport_height),
    )


def validate_norm_coordinate(value: int, field_name: str) -> int:
    if value < 0 or value > NORM_MAX:
        raise ValueError(f"{field_name} must be an integer from 0 to {NORM_MAX}")
    return value
