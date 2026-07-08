from __future__ import annotations

import json
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
from core.hover import (
    HOVER_ALIGNMENT_ACTION_TYPES,
    MAX_HOVER_ALIGNMENT_PASSES,
    action_triggers_hover,
    alignment_exhausted_blocked_action,
    derive_hover_alignment,
)
from core.refine import run_roi_refine
from core.formal_report import write_formal_reports
from core.publish import finalize_report_publish
from core.report import write_persona_report
from core.verification import execute_with_verification
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
            "action": action.to_trace_dict(
                viewport_width=frame.viewport_width,
                viewport_height=frame.viewport_height,
            ),
            "source": maker.source,
        },
        "execution": None,
    }
    if hover is not None:
        step_payload["hover"] = hover
    trace.add_step(step_payload)


def _hover_pass_suffix(pass_index: int) -> str:
    if pass_index == 0:
        return "-hover"
    return f"-hover-{pass_index + 1}"


def _hover_pass_record(
    *,
    config: TargetConfig,
    frame: ObservationFrame,
    maker: DecisionMaker,
    hover_action: Action,
    pass_index: int,
    execution: dict[str, Any] | None,
) -> dict[str, Any]:
    return {
        "pass": pass_index,
        "observation": _observation_dict(config, frame),
        "decision": {
            "action": hover_action.to_trace_dict(
                viewport_width=frame.viewport_width,
                viewport_height=frame.viewport_height,
            ),
            "source": maker.source,
        },
        "execution": execution,
    }


def _run_hover_confirmation(
    *,
    config: TargetConfig,
    adapter: BrowserPlatformAdapter,
    maker: DecisionMaker,
    step_index: int,
    pending_click: Action,
) -> tuple[Action, ObservationFrame, dict[str, Any] | None]:
    """Move to click target, align via hover sub-loop, then click or return terminal action."""
    assert pending_click.x is not None and pending_click.y is not None

    move_action = Action(
        type="move_to",
        x=pending_click.x,
        y=pending_click.y,
        reason=pending_click.reason,
        target_kind=pending_click.target_kind,
    )
    move_execution = execute_action(adapter, move_action)

    passes: list[dict[str, Any]] = []
    final_hover_action: Action | None = None
    final_hover_frame: ObservationFrame | None = None

    for pass_index in range(MAX_HOVER_ALIGNMENT_PASSES + 1):
        hover_frame = adapter.capture_frame(
            step=step_index,
            output_dir=config.output_dir,
            phase="hover",
            filename_suffix=_hover_pass_suffix(pass_index),
        )
        hover_action = maker.decide(
            config,
            hover_frame,
            step_index,
            phase="hover",
            pending_action=pending_click,
        )
        final_hover_action = hover_action
        final_hover_frame = hover_frame

        if is_terminal_action(hover_action):
            passes.append(
                _hover_pass_record(
                    config=config,
                    frame=hover_frame,
                    maker=maker,
                    hover_action=hover_action,
                    pass_index=pass_index,
                    execution=None,
                )
            )
            break

        if hover_action.type == "click_current":
            hover_execution = execute_with_verification(
                adapter,
                hover_action,
                output_dir=config.output_dir,
                step_index=step_index,
            )
            passes.append(
                _hover_pass_record(
                    config=config,
                    frame=hover_frame,
                    maker=maker,
                    hover_action=hover_action,
                    pass_index=pass_index,
                    execution=hover_execution,
                )
            )
            break

        if hover_action.type in HOVER_ALIGNMENT_ACTION_TYPES:
            hover_execution = execute_action(adapter, hover_action)
            passes.append(
                _hover_pass_record(
                    config=config,
                    frame=hover_frame,
                    maker=maker,
                    hover_action=hover_action,
                    pass_index=pass_index,
                    execution=hover_execution,
                )
            )
            if pass_index >= MAX_HOVER_ALIGNMENT_PASSES:
                break
            continue

        passes.append(
            _hover_pass_record(
                config=config,
                frame=hover_frame,
                maker=maker,
                hover_action=hover_action,
                pass_index=pass_index,
                execution=None,
            )
        )
        break

    if final_hover_action is None or final_hover_frame is None or not passes:
        raise BrowserAdapterError("Hover alignment finished without a recorded pass.")

    if final_hover_action.type in HOVER_ALIGNMENT_ACTION_TYPES:
        final_hover_action = alignment_exhausted_blocked_action(
            passes=len(passes),
            last_reason=passes[-1]["decision"]["action"].get("reason")
            if passes
            else None,
        )

    final_pass = passes[-1]
    if is_terminal_action(final_hover_action) and final_hover_action.type == "blocked":
        final_pass = {
            **final_pass,
            "decision": {
                "action": final_hover_action.to_trace_dict(
                    viewport_width=final_hover_frame.viewport_width,
                    viewport_height=final_hover_frame.viewport_height,
                ),
                "source": maker.source,
            },
            "execution": None,
        }
    alignment = derive_hover_alignment(
        pass_count=len(passes),
        final_action_type=final_hover_action.type,
        vlm_alignment=final_hover_action.alignment,
    )

    hover_block: dict[str, Any] = {
        "observation": final_pass["observation"],
        "intended_click": pending_click.to_trace_dict(
            viewport_width=final_hover_frame.viewport_width,
            viewport_height=final_hover_frame.viewport_height,
        ),
        "decision": final_pass["decision"],
        "execution": final_pass["execution"],
        "alignment_passes": len(passes),
    }
    if alignment is not None:
        hover_block["alignment"] = alignment
    target_kind = pending_click.target_kind or final_hover_action.target_kind
    if target_kind is not None:
        hover_block["target_kind"] = target_kind
    if len(passes) > 1:
        hover_block["adjustments"] = passes[:-1]

    return final_hover_action, final_hover_frame, {
        "move_execution": move_execution,
        "hover": hover_block,
    }


def run_visual_agent_loop(
    config: TargetConfig,
    *,
    decision_maker: DecisionMaker | None = None,
    persona_report_gemini: bool = False,
    gemini_api_key: str | None = None,
    gemini_model: str | None = None,
    run_id: str | None = None,
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
                refined_click, refine_trace = run_roi_refine(
                    maker=maker,
                    config=config,
                    frame=frame,
                    coarse=action,
                    step_index=step_index,
                )
                hover_action, hover_frame, hover_trace = _run_hover_confirmation(
                    config=config,
                    adapter=adapter,
                    maker=maker,
                    step_index=step_index,
                    pending_click=refined_click,
                )
                final_frame = hover_frame
                assert hover_trace is not None

                trace.add_step(
                    {
                        "step": step_index,
                        "observation": _observation_dict(config, frame),
                        "decision": {
                            "action": action.to_trace_dict(
                                viewport_width=frame.viewport_width,
                                viewport_height=frame.viewport_height,
                            ),
                            "source": maker.source,
                        },
                        "refine": refine_trace,
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
                        "action": action.to_trace_dict(
                            viewport_width=frame.viewport_width,
                            viewport_height=frame.viewport_height,
                        ),
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

    ux_result_payload = json.loads(artifacts.ux_result_path.read_text(encoding="utf-8"))
    use_gemini_synthesis = persona_report_gemini and maker.source != "stub"
    persona_report_path, report_result = write_persona_report(
        config,
        trace_payload=trace.to_dict(),
        ux_result=ux_result_payload,
        decision_source=maker.source,
        use_gemini_synthesis=use_gemini_synthesis,
        api_key=gemini_api_key,
        model_name=gemini_model,
    )
    ux_result_payload = json.loads(artifacts.ux_result_path.read_text(encoding="utf-8"))
    formal_result = write_formal_reports(
        config,
        trace_payload=trace.to_dict(),
        ux_result=ux_result_payload,
        decision_source=maker.source,
    )
    publish_result = finalize_report_publish(config.output_dir, run_id=run_id)
    artifacts = RunArtifacts(
        action_trace_path=artifacts.action_trace_path,
        ux_result_path=artifacts.ux_result_path,
        persona_report_path=persona_report_path,
        ux_report_path=formal_result.ux_report_path,
        index_html_path=formal_result.index_html_path,
        recording_path=artifacts.recording_path,
        report_synthesis=report_result.synthesis,
        run_id=publish_result.run_id,
        report_url=publish_result.report_url,
        report_base_url=publish_result.report_base_url,
        published_dir=publish_result.published_dir,
    )

    return LoopRunResult(
        terminal_state=terminal_state,
        summary=summary,
        main_finding=main_finding or summary,
        classifications=classifications,
        steps_taken=steps_taken,
        artifacts=artifacts,
    )
