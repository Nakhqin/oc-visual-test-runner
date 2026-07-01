from __future__ import annotations

import os

from adapters.browser import ObservationFrame
from core.actions import Action
from core.config import TargetConfig
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
                reason="Stub confirms hover target at marked pointer.",
            )
        if step_index == 0:
            return Action(
                type="click",
                x=frame.viewport_width // 2,
                y=frame.viewport_height // 2,
                reason="Stub moves to viewport center for hover-loop smoke test.",
            )
        return Action(type="blocked", reason=self._reason)


def create_decision_maker(*, use_stub: bool = False) -> StubDecisionMaker | GeminiDecisionMaker:
    if use_stub:
        return StubDecisionMaker()

    api_key = os.environ.get(ENV_GOOGLE_API_KEY, "").strip()
    if not api_key:
        return StubDecisionMaker()

    model_name = os.environ.get(ENV_GEMINI_MODEL, DEFAULT_GEMINI_MODEL).strip()
    return GeminiDecisionMaker(api_key=api_key, model_name=model_name or DEFAULT_GEMINI_MODEL)
