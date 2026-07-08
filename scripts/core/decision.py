from __future__ import annotations

import os

from pathlib import Path

from adapters.browser import ObservationFrame
from core.actions import Action
from core.config import TargetConfig
from core.refine import CropRegion
from core.vlm import ENV_GEMINI_MODEL, ENV_GOOGLE_API_KEY, DEFAULT_GEMINI_MODEL, GeminiDecisionMaker

STUB_BLOCKED_REASON = (
    "VLM integration is not configured; set GOOGLE_API_KEY or pass --use-stub explicitly."
)


class StubDecisionMaker:
    """Placeholder decision maker when Gemini is unavailable or forced via --use-stub."""

    source = "stub"

    def __init__(self, *, reason: str = STUB_BLOCKED_REASON) -> None:
        self._reason = reason

    def decide(
        self,
        config: TargetConfig,
        frame: ObservationFrame,
        step_index: int,
        *,
        phase: str = "observe",
        pending_action: Action | None = None,
    ) -> Action:
        _ = config, frame, pending_action
        if phase == "hover":
            return Action(
                type="click_current",
                alignment="aligned",
                reason="Stub confirms hover target at marked pointer.",
            )
        if step_index == 0:
            return Action(
                type="click",
                x=500,
                y=500,
                target_kind="button",
                reason="Stub moves to viewport center for hover-loop smoke test.",
            )
        return Action(type="blocked", reason=self._reason)

    def refine_click_coordinates(
        self,
        config: TargetConfig,
        frame: ObservationFrame,
        coarse: Action,
        step_index: int,
        *,
        crop_image_path: Path,
        crop_region: CropRegion,
    ) -> Action:
        _ = config, frame, step_index, crop_image_path, crop_region
        if coarse.x is None or coarse.y is None:
            return coarse
        return Action(
            type="click",
            x=coarse.x,
            y=coarse.y,
            reason=coarse.reason,
            target_kind=coarse.target_kind,
        )


def create_decision_maker(*, use_stub: bool = False) -> StubDecisionMaker | GeminiDecisionMaker:
    if use_stub:
        return StubDecisionMaker()

    api_key = os.environ.get(ENV_GOOGLE_API_KEY, "").strip()
    if not api_key:
        return StubDecisionMaker()

    model_name = os.environ.get(ENV_GEMINI_MODEL, DEFAULT_GEMINI_MODEL).strip()
    return GeminiDecisionMaker(api_key=api_key, model_name=model_name or DEFAULT_GEMINI_MODEL)
