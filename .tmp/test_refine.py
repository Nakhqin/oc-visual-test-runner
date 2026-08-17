"""Unit tests for UVG L1 ROI refine coordinate mapping."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from core.actions import Action
from core.refine import (
    CROP_VIEWPORT_FRACTION,
    TIGHT_CROP_VIEWPORT_FRACTION,
    TIGHT_MIN_CROP_SIZE,
    CropRegion,
    compute_crop_region,
    crop_norm_to_global_norm,
    crop_profile_for_action,
    uses_tight_refine_crop,
)


def test_compute_crop_region_size() -> None:
    crop = compute_crop_region(640, 450, 1280, 900)
    assert crop.width == max(240, round(1280 * CROP_VIEWPORT_FRACTION))
    assert crop.height == max(240, round(900 * CROP_VIEWPORT_FRACTION))
    assert 0 <= crop.left <= 1280 - crop.width
    assert 0 <= crop.top <= 900 - crop.height


def test_compute_tight_crop_region_size() -> None:
    crop = compute_crop_region(
        400,
        600,
        1280,
        900,
        fraction=TIGHT_CROP_VIEWPORT_FRACTION,
        min_size=TIGHT_MIN_CROP_SIZE,
    )
    assert crop.width == max(TIGHT_MIN_CROP_SIZE, round(1280 * TIGHT_CROP_VIEWPORT_FRACTION))
    assert crop.height == max(TIGHT_MIN_CROP_SIZE, round(900 * TIGHT_CROP_VIEWPORT_FRACTION))
    assert crop.width < max(240, round(1280 * CROP_VIEWPORT_FRACTION))


def test_crop_profile_button_is_tight() -> None:
    action = Action(type="click", x=300, y=700, target_kind="button", reason="digit 1")
    assert uses_tight_refine_crop(action) is True
    fraction, min_size, profile = crop_profile_for_action(action)
    assert profile == "tight"
    assert fraction == TIGHT_CROP_VIEWPORT_FRACTION
    assert min_size == TIGHT_MIN_CROP_SIZE


def test_crop_profile_text_default() -> None:
    action = Action(type="click", x=500, y=400, target_kind="text", reason="language row")
    assert uses_tight_refine_crop(action) is False
    _, _, profile = crop_profile_for_action(action)
    assert profile == "default"


def test_crop_profile_password_reason_tight() -> None:
    action = Action(type="click", x=500, y=700, reason="Enter PIN on 安全键盘")
    assert uses_tight_refine_crop(action) is True


def test_crop_center_maps_to_global_center() -> None:
    vw, vh = 1280, 900
    center_x, center_y = 640, 450
    crop = compute_crop_region(center_x, center_y, vw, vh)
    local_center_x = 500
    local_center_y = 500
    global_x, global_y = crop_norm_to_global_norm(
        local_center_x,
        local_center_y,
        crop,
        vw,
        vh,
    )
    # center of crop in local 500,500 should map near crop center in global space
    from core.coordinates import norm_coords_to_pixels

    gx, gy = norm_coords_to_pixels(global_x, global_y, vw, vh)
    assert abs(gx - (crop.left + crop.width // 2)) <= 2
    assert abs(gy - (crop.top + crop.height // 2)) <= 2


def test_crop_norm_corners() -> None:
    crop = CropRegion(left=100, top=50, width=320, height=240)
    from core.coordinates import norm_to_pixel

    local_x_px = norm_to_pixel(1000, crop.width)
    local_y_px = norm_to_pixel(1000, crop.height)
    assert crop.left + local_x_px == 419
    assert crop.top + local_y_px == 289


def main() -> None:
    test_compute_crop_region_size()
    test_compute_tight_crop_region_size()
    test_crop_profile_button_is_tight()
    test_crop_profile_text_default()
    test_crop_profile_password_reason_tight()
    test_crop_center_maps_to_global_center()
    test_crop_norm_corners()
    print("refine unit tests OK")


if __name__ == "__main__":
    main()
