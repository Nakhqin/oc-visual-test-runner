from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Protocol

from adapters.browser import (
    BrowserAdapterError,
    BrowserPlatformAdapter,
    ObservationFrame,
    RECORDING_FILENAME,
)
from core.actions import Action, is_terminal_action
from core.config import TargetConfig
from core.decision import StubDecisionMaker
from core.executor import execute_action
from core.verification import execute_with_verification
from core.hover import action_triggers_hover
from core.writers import RunArtifacts, TraceBuilder, write_loop_artifacts


class DecisionMaker(Protocol):
    source: str

    def decide(
        self,
        config: TargetConfig,
        frame: ObservationFrame,
        step_index: int,
        *,
        phase: str = "observe",
        pending_action: Action | None = None,
    ) -> Action: ...


@dataclass(frozen=True)
class LoopRunResult:
    terminal_state: str
    summary: str
    main_finding: str
    classifications: list[str]
    steps_taken: int
    artifacts: RunArtifacts


def _observation_dict(config: TargetConfig, frame: ObservationFrame) -> dict[str, Any]:
    return {
        "screenshot": frame.image_path.relative_to(config.output_dir).as_posix(),
        "page_url": frame.url,
        "viewport_width": frame.viewport_width,
        "viewport_height": frame.viewport_height,
        "cursor": {"x": frame.cursor_x, "y": frame.cursor_y},
        "phase": frame.phase,
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


def _classifications_for_terminal(
    terminal_state: str,
    action: Action | None,
    *,
    decision_source: str,
) -> list[str]:
    if terminal_state == "timeout":
        return ["system-runtime issue"]
    if terminal_state == "max_steps":
        return []
    if terminal_state != "blocked" or action is None:
        return []
    if decision_source == "stub":
        return ["automation limitation"]
    if action.reason and action.reason.startswith("VLM"):
        return ["system-runtime issue"]
    return []


def _record_terminal_step(
    trace: TraceBuilder,
    *,
    config: TargetConfig,
    frame: ObservationFrame,
    step_index: int,
    maker: DecisionMaker,
    action: Action,
    hover: dict[str, Any] | None = None,
) -> None:
    step_payload: dict[str, Any] = {
        "step": step_index,
        "observation": _observation_dict(config, frame),
        "decision": {
            "action": action.to_dict(),
            "source": maker.source,
        },
        "execution": None,
    }
    if hover is not None:
        step_payload["hover"] = hover
    trace.add_step(step_payload)


def _run_hover_confirmation(
    *,
    config: TargetConfig,
    adapter: BrowserPlatformAdapter,
    maker: DecisionMaker,
    step_index: int,
    pending_click: Action,
) -> tuple[Action, ObservationFrame, dict[str, Any] | None]:
    """Move to click target, capture hover frame, and return hover-phase outcome."""
    assert pending_click.x is not None and pending_click.y is not None

    move_action = Action(
        type="move_to",
        x=pending_click.x,
        y=pending_click.y,
        reason=pending_click.reason,
    )
    move_execution = execute_action(adapter, move_action)

    hover_frame = adapter.capture_frame(
        step=step_index,
        output_dir=config.output_dir,
        phase="hover",
        filename_suffix="-hover",
    )
    hover_action = maker.decide(
        config,
        hover_frame,
        step_index,
        phase="hover",
        pending_action=pending_click,
    )

    hover_block: dict[str, Any] = {
        "observation": _observation_dict(config, hover_frame),
        "intended_click": {"x": pending_click.x, "y": pending_click.y},
        "decision": {
            "action": hover_action.to_dict(),
            "source": maker.source,
        },
        "execution": None,
    }

    if is_terminal_action(hover_action):
        hover_block["execution"] = None
        return hover_action, hover_frame, {
            "move_execution": move_execution,
            "hover": hover_block,
        }

    hover_execution = execute_with_verification(
        adapter,
        hover_action,
        output_dir=config.output_dir,
        step_index=step_index,
    )
    hover_block["execution"] = hover_execution
    return hover_action, hover_frame, {
        "move_execution": move_execution,
        "hover": hover_block,
    }


def run_visual_agent_loop(
    config: TargetConfig,
    *,
    decision_maker: DecisionMaker | None = None,
) -> LoopRunResult:
    """Run observe → decide → hover (when clicking) → act → record until a terminal state."""
    config.output_dir.mkdir(parents=True, exist_ok=True)
    maker = decision_maker or StubDecisionMaker()
    trace = TraceBuilder(config)
    navigation_timeout_ms = max(config.timeout_seconds, 1) * 1000
    deadline = time.monotonic() + config.timeout_seconds

    terminal_state = "max_steps"
    terminal_action: Action | None = None
    steps_taken = 0
    final_frame: ObservationFrame | None = None

    recording_path = config.output_dir / RECORDING_FILENAME

    with BrowserPlatformAdapter(
        navigation_timeout_ms=navigation_timeout_ms,
        record_video_path=recording_path,
    ) as adapter:
        adapter.open(config.url, target=config.target)

        for step_index in range(config.max_steps):
            if time.monotonic() >= deadline:
                terminal_state = "timeout"
                break

            frame = adapter.capture_frame(step=step_index, output_dir=config.output_dir)
            final_frame = frame
            action = maker.decide(config, frame, step_index)
            steps_taken = step_index + 1

            if is_terminal_action(action):
                _record_terminal_step(
                    trace,
                    config=config,
                    frame=frame,
                    step_index=step_index,
                    maker=maker,
                    action=action,
                )
                terminal_state = action.type
                terminal_action = action
                break

            if action_triggers_hover(action):
                hover_action, hover_frame, hover_trace = _run_hover_confirmation(
                    config=config,
                    adapter=adapter,
                    maker=maker,
                    step_index=step_index,
                    pending_click=action,
                )
                final_frame = hover_frame
                assert hover_trace is not None

                trace.add_step(
                    {
                        "step": step_index,
                        "observation": _observation_dict(config, frame),
                        "decision": {
                            "action": action.to_dict(),
                            "source": maker.source,
                        },
                        "execution": hover_trace["move_execution"],
                        "hover": hover_trace["hover"],
                    }
                )

                if is_terminal_action(hover_action):
                    terminal_state = hover_action.type
                    terminal_action = hover_action
                    break

                adapter.pause_for_feedback()
                continue

            execution = execute_with_verification(
                adapter,
                action,
                output_dir=config.output_dir,
                step_index=step_index,
            )
            trace.add_step(
                {
                    "step": step_index,
                    "observation": _observation_dict(config, frame),
                    "decision": {
                        "action": action.to_dict(),
                        "source": maker.source,
                    },
                    "execution": execution,
                }
            )
            adapter.pause_for_feedback()

    finalized_recording = adapter.recording_path

    summary, main_finding = _summary_for_terminal(terminal_state, terminal_action)
    classifications = _classifications_for_terminal(
        terminal_state,
        terminal_action,
        decision_source=maker.source,
    )

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
        recording_path=finalized_recording,
    )

    return LoopRunResult(
        terminal_state=terminal_state,
        summary=summary,
        main_finding=main_finding or summary,
        classifications=classifications,
        steps_taken=steps_taken,
        artifacts=artifacts,
    )
