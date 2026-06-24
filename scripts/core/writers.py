"""JSON schemas and writers for run artifacts."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from adapters.browser import ObservationFrame
from core.config import TargetConfig

SCHEMA_VERSION = "1"
TERMINAL_BLOCKED = "blocked"


@dataclass(frozen=True)
class RunArtifacts:
    action_trace_path: Path
    ux_result_path: Path


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def build_action_trace(config: TargetConfig, frame: ObservationFrame) -> dict[str, Any]:
    screenshot_ref = frame.image_path.relative_to(config.output_dir).as_posix()
    return {
        "schema_version": SCHEMA_VERSION,
        "created_at": _utc_now_iso(),
        "target": config.target,
        "url": config.url,
        "persona": config.persona,
        "goal": config.goal,
        "adapter": "browser",
        "runner": "visual_agent",
        "steps": [
            {
                "step": frame.step,
                "phase": "observation",
                "action": None,
                "observation": {
                    "screenshot": screenshot_ref,
                    "page_url": frame.url,
                    "viewport_width": frame.viewport_width,
                    "viewport_height": frame.viewport_height,
                },
                "note": "Initial observation frame captured before agent loop.",
            }
        ],
    }


def build_ux_result(
    config: TargetConfig,
    frame: ObservationFrame,
    *,
    terminal_state: str = TERMINAL_BLOCKED,
) -> dict[str, Any]:
    screenshot_ref = frame.image_path.relative_to(config.output_dir).as_posix()
    return {
        "schema_version": SCHEMA_VERSION,
        "created_at": _utc_now_iso(),
        "target": config.target,
        "url": config.url,
        "persona": config.persona,
        "goal": config.goal,
        "terminal_state": terminal_state,
        "summary": (
            "Initial observation frame captured. "
            "Visual agent loop is not implemented yet."
        ),
        "main_finding": (
            "The runner opened the target and captured a screenshot, "
            "but cannot continue the persona walkthrough until the agent loop ships."
        ),
        "classifications": [],
        "adapter": "browser",
        "runner": "visual_agent",
        "output_dir": str(config.output_dir),
        "artifacts": {
            "action_trace": "action_trace.json",
            "ux_result": "ux_result.json",
            "screenshots_dir": "screenshots/",
            "recording": None,
            "initial_screenshot": screenshot_ref,
        },
        "limits": {
            "max_steps": config.max_steps,
            "timeout_seconds": config.timeout_seconds,
            "steps_taken": 0,
        },
    }


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def write_run_artifacts(config: TargetConfig, frame: ObservationFrame) -> RunArtifacts:
    action_trace_path = config.output_dir / "action_trace.json"
    ux_result_path = config.output_dir / "ux_result.json"
    _write_json(action_trace_path, build_action_trace(config, frame))
    _write_json(ux_result_path, build_ux_result(config, frame))
    return RunArtifacts(
        action_trace_path=action_trace_path,
        ux_result_path=ux_result_path,
    )
