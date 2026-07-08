"""Unit tests for UVG L1 ROI refine coordinate mapping."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from core.refine import (
    CROP_VIEWPORT_FRACTION,
    CropRegion,
    compute_crop_region,
    crop_norm_to_global_norm,
)


def test_compute_crop_region_size() -> None:
    crop = compute_crop_region(640, 450, 1280, 900)
    assert crop.width == max(240, round(1280 * CROP_VIEWPORT_FRACTION))
    assert crop.height == max(240, round(900 * CROP_VIEWPORT_FRACTION))
    assert 0 <= crop.left <= 1280 - crop.width
    assert 0 <= crop.top <= 900 - crop.height


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
    test_crop_center_maps_to_global_center()
    test_crop_norm_corners()
    print("refine unit tests OK")


if __name__ == "__main__":
    main()
