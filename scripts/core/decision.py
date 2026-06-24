from __future__ import annotations

from adapters.browser import ObservationFrame
from core.actions import Action
from core.config import TargetConfig

STUB_BLOCKED_REASON = (
    "VLM integration is not implemented yet; the runner cannot decide persona actions."
)


class StubDecisionMaker:
    """Placeholder decision maker until Gemini VLM integration lands."""

    source = "stub"

    def decide(
        self,
        config: TargetConfig,
        frame: ObservationFrame,
        step_index: int,
    ) -> Action:
        _ = config, frame, step_index
        return Action(type="blocked", reason=STUB_BLOCKED_REASON)
