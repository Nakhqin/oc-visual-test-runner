"""Unit tests for normalized coordinate mapping (G1)."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from core.actions import Action, ActionParseError, parse_action_payload
from core.coordinates import (
    NORM_MAX,
    norm_coords_to_pixels,
    norm_to_pixel,
    pixel_to_norm,
    validate_norm_coordinate,
)


def test_corners_1280x900() -> None:
    assert norm_coords_to_pixels(0, 0, 1280, 900) == (0, 0)
    assert norm_coords_to_pixels(1000, 1000, 1280, 900) == (1279, 899)


def test_center_mapping() -> None:
    vw, vh = 1280, 900
    x_px, y_px = norm_coords_to_pixels(500, 500, vw, vh)
    assert x_px == 640
    assert y_px == 450


def test_pixel_round_trip() -> None:
    vw, vh = 1280, 900
    for x_px, y_px in ((0, 0), (1279, 899), (640, 450)):
        x_norm = pixel_to_norm(x_px, vw)
        y_norm = pixel_to_norm(y_px, vh)
        assert norm_coords_to_pixels(x_norm, y_norm, vw, vh) == (x_px, y_px)


def test_norm_to_pixel_formula() -> None:
    assert norm_to_pixel(500, 1280) == 640
    assert norm_to_pixel(500, 900) == 450


def test_validate_norm_coordinate() -> None:
    validate_norm_coordinate(0, "x")
    validate_norm_coordinate(1000, "y")
    try:
        validate_norm_coordinate(1001, "x")
        raise AssertionError("expected ValueError")
    except ValueError as exc:
        assert "0 to 1000" in str(exc)


def test_parse_action_accepts_norm_coords() -> None:
    action = parse_action_payload(
        {"type": "click", "x": 500, "y": 350, "reason": "test"}
    )
    assert action.x == 500
    assert action.y == 350


def test_parse_action_rejects_out_of_range_coords() -> None:
    try:
        parse_action_payload(
            {"type": "click", "x": 1500, "y": 200, "reason": "out of range"}
        )
        raise AssertionError("expected ActionParseError")
    except ActionParseError as exc:
        assert "0 to 1000" in str(exc)


def test_action_to_trace_dict_includes_pixels() -> None:
    action = Action(type="click", x=500, y=500, reason="center")
    trace = action.to_trace_dict(viewport_width=1280, viewport_height=900)
    assert trace["x"] == 500
    assert trace["y"] == 500
    assert trace["x_px"] == 640
    assert trace["y_px"] == 450
    assert trace["coordinate_space"] == "norm_1000"


def main() -> None:
    test_corners_1280x900()
    test_center_mapping()
    test_pixel_round_trip()
    test_norm_to_pixel_formula()
    test_validate_norm_coordinate()
    test_parse_action_accepts_norm_coords()
    test_parse_action_rejects_out_of_range_coords()
    test_action_to_trace_dict_includes_pixels()
    print("coordinates unit tests OK")


if __name__ == "__main__":
    main()
