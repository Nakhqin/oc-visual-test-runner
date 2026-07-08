"""UVG L1 — ROI crop refine: local VLM pointing mapped back to viewport coordinates."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

from adapters.browser import ObservationFrame
from core.actions import Action, ActionParseError, extract_json_object
from core.config import TargetConfig
from core.coordinates import norm_coords_to_pixels, norm_to_pixel, pixel_to_norm

CROP_VIEWPORT_FRACTION = 0.25
MIN_CROP_SIZE = 240
CROP_COORDINATE_SPACE = "norm_1000_local"


@dataclass(frozen=True)
class CropRegion:
    left: int
    top: int
    width: int
    height: int

    def to_dict(self) -> dict[str, int]:
        return {
            "left": self.left,
            "top": self.top,
            "width": self.width,
            "height": self.height,
        }


class RefineDecisionMaker(Protocol):
    source: str

    def refine_click_coordinates(
        self,
        config: TargetConfig,
        frame: ObservationFrame,
        coarse: Action,
        step_index: int,
        *,
        crop_image_path: Path,
        crop_region: CropRegion,
    ) -> Action: ...


def _clamp(value: int, low: int, high: int) -> int:
    return max(low, min(value, high))


def compute_crop_region(
    center_x_px: int,
    center_y_px: int,
    viewport_width: int,
    viewport_height: int,
) -> CropRegion:
    crop_width = max(MIN_CROP_SIZE, round(viewport_width * CROP_VIEWPORT_FRACTION))
    crop_height = max(MIN_CROP_SIZE, round(viewport_height * CROP_VIEWPORT_FRACTION))
    crop_width = min(crop_width, viewport_width)
    crop_height = min(crop_height, viewport_height)

    left = _clamp(center_x_px - crop_width // 2, 0, viewport_width - crop_width)
    top = _clamp(center_y_px - crop_height // 2, 0, viewport_height - crop_height)
    return CropRegion(left=left, top=top, width=crop_width, height=crop_height)


def crop_norm_to_global_norm(
    x_norm: int,
    y_norm: int,
    crop: CropRegion,
    viewport_width: int,
    viewport_height: int,
) -> tuple[int, int]:
    local_x_px = norm_to_pixel(x_norm, crop.width)
    local_y_px = norm_to_pixel(y_norm, crop.height)
    global_x_px = crop.left + local_x_px
    global_y_px = crop.top + local_y_px
    return (
        pixel_to_norm(global_x_px, viewport_width),
        pixel_to_norm(global_y_px, viewport_height),
    )


def save_crop_screenshot(source: Path, dest: Path, crop: CropRegion) -> None:
    try:
        from PIL import Image
    except ImportError as exc:
        raise RuntimeError(
            "Pillow is not installed. Run: pip install -r requirements.txt"
        ) from exc

    dest.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(source) as image:
        box = (
            crop.left,
            crop.top,
            crop.left + crop.width,
            crop.top + crop.height,
        )
        cropped = image.crop(box)
        cropped.save(dest, format="PNG")


def parse_refine_payload(payload: dict[str, Any]) -> tuple[int, int, str | None]:
    x = payload.get("x")
    y = payload.get("y")
    if not isinstance(x, int) or not isinstance(y, int):
        raise ActionParseError("refine response requires integer x and y")
    if x < 0 or x > 1000 or y < 0 or y > 1000:
        raise ActionParseError("refine x and y must be integers from 0 to 1000")
    reason = payload.get("reason")
    if reason is not None and not isinstance(reason, str):
        raise ActionParseError("refine reason must be a string when provided")
    return x, y, reason.strip() if isinstance(reason, str) else None


def refine_crop_filename_suffix() -> str:
    return "-refine-crop"


def run_roi_refine(
    *,
    maker: RefineDecisionMaker,
    config: TargetConfig,
    frame: ObservationFrame,
    coarse: Action,
    step_index: int,
) -> tuple[Action, dict[str, Any]]:
    """L1: crop around coarse point, refine coordinates, return click Action + trace block."""
    if coarse.x is None or coarse.y is None:
        raise ValueError("coarse click requires x and y")

    viewport_width = frame.viewport_width
    viewport_height = frame.viewport_height
    center_x_px, center_y_px = norm_coords_to_pixels(
        coarse.x,
        coarse.y,
        viewport_width,
        viewport_height,
    )
    crop = compute_crop_region(
        center_x_px,
        center_y_px,
        viewport_width,
        viewport_height,
    )
    crop_path = frame.image_path.parent / (
        f"step-{step_index:03d}{refine_crop_filename_suffix()}.png"
    )
    save_crop_screenshot(frame.image_path, crop_path, crop)

    refined = maker.refine_click_coordinates(
        config,
        frame,
        coarse,
        step_index,
        crop_image_path=crop_path,
        crop_region=crop,
    )
    if refined.type != "click" or refined.x is None or refined.y is None:
        refined = Action(
            type="click",
            x=coarse.x,
            y=coarse.y,
            reason=coarse.reason,
            target_kind=coarse.target_kind,
        )
        refine_failed = True
    else:
        refine_failed = False

    trace_block: dict[str, Any] = {
        "coarse": coarse.to_trace_dict(
            viewport_width=viewport_width,
            viewport_height=viewport_height,
        ),
        "fine": refined.to_trace_dict(
            viewport_width=viewport_width,
            viewport_height=viewport_height,
        ),
        "crop": {
            **crop.to_dict(),
            "screenshot": crop_path.relative_to(config.output_dir).as_posix(),
            "coordinate_space": CROP_COORDINATE_SPACE,
            "center_px": {"x": center_x_px, "y": center_y_px},
        },
        "source": maker.source,
        "fallback_to_coarse": refine_failed,
    }
    return refined, trace_block
