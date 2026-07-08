"""JSON schemas and writers for run artifacts."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from adapters.browser import ObservationFrame
from core.config import TargetConfig

SCHEMA_VERSION = "2"
COORDINATE_SPACE_NORM_1000 = "norm_1000"
GROUNDING_MODE_UVG = "uvg"


@dataclass(frozen=True)
class RunArtifacts:
    action_trace_path: Path
    ux_result_path: Path
    persona_report_path: Path | None
    ux_report_path: Path | None
    index_html_path: Path | None
    recording_path: Path | None
    report_synthesis: str | None = None
    run_id: str | None = None
    report_url: str | None = None
    report_base_url: str | None = None
    published_dir: Path | None = None


class TraceBuilder:
    def __init__(self, config: TargetConfig) -> None:
        self._config = config
        self._steps: list[dict[str, Any]] = []

    def add_step(self, step: dict[str, Any]) -> None:
        self._steps.append(step)

    @property
    def steps(self) -> list[dict[str, Any]]:
        return list(self._steps)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": SCHEMA_VERSION,
            "coordinate_space": COORDINATE_SPACE_NORM_1000,
            "grounding": GROUNDING_MODE_UVG,
            "created_at": _utc_now_iso(),
            "target": self._config.target,
            "url": self._config.url,
            "persona": self._config.persona,
            "goal": self._config.goal,
            "adapter": "browser",
            "runner": "visual_agent",
            "steps": self._steps,
        }


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def build_ux_result(
    config: TargetConfig,
    final_frame: ObservationFrame,
    *,
    terminal_state: str,
    summary: str,
    main_finding: str,
    classifications: list[str],
    steps_taken: int,
    recording_path: Path | None = None,
) -> dict[str, Any]:
    screenshot_ref = final_frame.image_path.relative_to(config.output_dir).as_posix()
    recording_ref = (
        recording_path.relative_to(config.output_dir).as_posix()
        if recording_path is not None and recording_path.exists()
        else None
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "created_at": _utc_now_iso(),
        "target": config.target,
        "url": config.url,
        "persona": config.persona,
        "goal": config.goal,
        "terminal_state": terminal_state,
        "summary": summary,
        "main_finding": main_finding,
        "classifications": classifications,
        "adapter": "browser",
        "runner": "visual_agent",
        "output_dir": str(config.output_dir),
        "artifacts": {
            "action_trace": "action_trace.json",
            "ux_result": "ux_result.json",
            "screenshots_dir": "screenshots/",
            "recording": recording_ref,
            "initial_screenshot": screenshot_ref,
        },
        "limits": {
            "max_steps": config.max_steps,
            "timeout_seconds": config.timeout_seconds,
            "steps_taken": steps_taken,
        },
    }


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def write_loop_artifacts(
    config: TargetConfig,
    trace: TraceBuilder,
    *,
    final_frame: ObservationFrame,
    terminal_state: str,
    summary: str,
    main_finding: str,
    classifications: list[str],
    steps_taken: int,
    recording_path: Path | None = None,
) -> RunArtifacts:
    action_trace_path = config.output_dir / "action_trace.json"
    ux_result_path = config.output_dir / "ux_result.json"
    _write_json(action_trace_path, trace.to_dict())
    _write_json(
        ux_result_path,
        build_ux_result(
            config,
            final_frame,
            terminal_state=terminal_state,
            summary=summary,
            main_finding=main_finding,
            classifications=classifications,
            steps_taken=steps_taken,
            recording_path=recording_path,
        ),
    )
    return RunArtifacts(
        action_trace_path=action_trace_path,
        ux_result_path=ux_result_path,
        persona_report_path=None,
        ux_report_path=None,
        index_html_path=None,
        recording_path=recording_path if recording_path and recording_path.exists() else None,
    )
