from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Protocol

from adapters.browser import BrowserAdapterError, BrowserPlatformAdapter, ObservationFrame
from core.actions import Action, is_terminal_action
from core.config import TargetConfig
from core.decision import StubDecisionMaker
from core.writers import RunArtifacts, TraceBuilder, write_loop_artifacts


class DecisionMaker(Protocol):
    source: str

    def decide(
        self,
        config: TargetConfig,
        frame: ObservationFrame,
        step_index: int,
    ) -> Action: ...


@dataclass(frozen=True)
class LoopRunResult:
    terminal_state: str
    summary: str
    main_finding: str
    classifications: list[str]
    steps_taken: int
    artifacts: RunArtifacts


def _observation_dict(config: TargetConfig, frame: ObservationFrame) -> dict:
    return {
        "screenshot": frame.image_path.relative_to(config.output_dir).as_posix(),
        "page_url": frame.url,
        "viewport_width": frame.viewport_width,
        "viewport_height": frame.viewport_height,
    }


def _summary_for_terminal(terminal_state: str, action: Action | None) -> tuple[str, str]:
    if terminal_state == "blocked" and action and action.reason:
        summary = f"Walkthrough stopped: {action.reason}"
        return summary, action.reason
    if terminal_state == "done":
        return "Walkthrough completed successfully.", action.reason if action else ""
    if terminal_state == "timeout":
        return (
            "Walkthrough stopped: overall timeout exceeded.",
            "The run exceeded timeout_seconds before reaching a terminal action.",
        )
    if terminal_state == "max_steps":
        return (
            "Walkthrough stopped: max_steps reached.",
            "The agent loop exhausted max_steps without a done or blocked action.",
        )
    return "Walkthrough ended.", ""


def run_visual_agent_loop(
    config: TargetConfig,
    *,
    decision_maker: DecisionMaker | None = None,
) -> LoopRunResult:
    """Run observe → decide → record until a terminal state or limit."""
    config.output_dir.mkdir(parents=True, exist_ok=True)
    maker = decision_maker or StubDecisionMaker()
    trace = TraceBuilder(config)
    navigation_timeout_ms = max(config.timeout_seconds, 1) * 1000
    deadline = time.monotonic() + config.timeout_seconds

    terminal_state = "max_steps"
    terminal_action: Action | None = None
    steps_taken = 0
    final_frame: ObservationFrame | None = None
    classifications: list[str] = []

    with BrowserPlatformAdapter(navigation_timeout_ms=navigation_timeout_ms) as adapter:
        adapter.open(config.url, target=config.target)

        for step_index in range(config.max_steps):
            if time.monotonic() >= deadline:
                terminal_state = "timeout"
                break

            frame = adapter.capture_frame(step=step_index, output_dir=config.output_dir)
            final_frame = frame
            action = maker.decide(config, frame, step_index)
            steps_taken = step_index + 1

            trace.add_step(
                {
                    "step": step_index,
                    "observation": _observation_dict(config, frame),
                    "decision": {
                        "action": action.to_dict(),
                        "source": maker.source,
                    },
                    "execution": None,
                }
            )

            if is_terminal_action(action):
                terminal_state = action.type
                terminal_action = action
                if terminal_state == "blocked" and maker.source == "stub":
                    classifications = ["automation limitation"]
                break

    summary, main_finding = _summary_for_terminal(terminal_state, terminal_action)
    if terminal_state == "timeout":
        classifications = ["system-runtime issue"]
    elif terminal_state == "max_steps":
        classifications = []

    if final_frame is None:
        raise BrowserAdapterError("Visual agent loop finished without capturing a frame.")

    artifacts = write_loop_artifacts(
        config,
        trace,
        final_frame=final_frame,
        terminal_state=terminal_state,
        summary=summary,
        main_finding=main_finding or summary,
        classifications=classifications,
        steps_taken=steps_taken,
    )

    return LoopRunResult(
        terminal_state=terminal_state,
        summary=summary,
        main_finding=main_finding or summary,
        classifications=classifications,
        steps_taken=steps_taken,
        artifacts=artifacts,
    )
