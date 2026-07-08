from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any

from core.coordinates import (
    COORDINATE_SPACE,
    norm_coords_to_pixels,
    validate_norm_coordinate,
)

SUPPORTED_ACTION_TYPES = frozenset(
    {
        "move_to",
        "move_by_delta",
        "click",
        "click_current",
        "scroll",
        "wait",
        "type",
        "done",
        "blocked",
    }
)
TERMINAL_ACTIONS = frozenset({"done", "blocked", "max_steps", "timeout"})
COORDINATE_ACTION_TYPES = frozenset({"move_to", "click"})
HOVER_TARGET_KINDS = frozenset({"text", "icon", "composite", "button"})


class ActionParseError(ValueError):
    """Raised when VLM output cannot be parsed into an Action."""


@dataclass(frozen=True)
class Action:
    type: str
    reason: str | None = None
    x: int | None = None
    y: int | None = None
    delta_x: int | None = None
    delta_y: int | None = None
    text: str | None = None
    wait_ms: int | None = None
    target_kind: str | None = None
    alignment: str | None = None

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {"type": self.type}
        if self.reason is not None:
            payload["reason"] = self.reason
        if self.x is not None:
            payload["x"] = self.x
        if self.y is not None:
            payload["y"] = self.y
        if self.delta_x is not None:
            payload["delta_x"] = self.delta_x
        if self.delta_y is not None:
            payload["delta_y"] = self.delta_y
        if self.text is not None:
            payload["text"] = self.text
        if self.wait_ms is not None:
            payload["wait_ms"] = self.wait_ms
        if self.target_kind is not None:
            payload["target_kind"] = self.target_kind
        if self.alignment is not None:
            payload["alignment"] = self.alignment
        return payload

    def to_trace_dict(
        self,
        *,
        viewport_width: int | None = None,
        viewport_height: int | None = None,
    ) -> dict[str, Any]:
        """Serialize for action_trace.json with optional pixel mapping."""
        payload = self.to_dict()
        if (
            self.x is not None
            and self.y is not None
            and viewport_width is not None
            and viewport_height is not None
        ):
            x_px, y_px = norm_coords_to_pixels(
                self.x,
                self.y,
                viewport_width,
                viewport_height,
            )
            payload["x_px"] = x_px
            payload["y_px"] = y_px
            payload["coordinate_space"] = COORDINATE_SPACE
        return payload


def is_terminal_action(action: Action) -> bool:
    return action.type in TERMINAL_ACTIONS


def _optional_int(value: Any, field_name: str) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int):
        raise ActionParseError(f"{field_name} must be an integer")
    return value


def _optional_str(value: Any, field_name: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        raise ActionParseError(f"{field_name} must be a non-empty string")
    return value.strip()


def _validate_coordinate_fields(action_type: str, x: int | None, y: int | None) -> None:
    if action_type not in COORDINATE_ACTION_TYPES:
        return
    if x is None or y is None:
        raise ActionParseError(f"{action_type} requires x and y")
    try:
        validate_norm_coordinate(x, "x")
        validate_norm_coordinate(y, "y")
    except ValueError as exc:
        raise ActionParseError(str(exc)) from exc


def _optional_target_kind(value: Any) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        raise ActionParseError("target_kind must be a non-empty string when provided")
    normalized = value.strip().lower()
    if normalized not in HOVER_TARGET_KINDS:
        allowed = ", ".join(sorted(HOVER_TARGET_KINDS))
        raise ActionParseError(f"target_kind must be one of: {allowed}")
    return normalized


def _optional_alignment(value: Any) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        raise ActionParseError("alignment must be a non-empty string when provided")
    normalized = value.strip().lower()
    allowed = {"aligned", "adjusted", "clicked_off_target", "unresolved"}
    if normalized not in allowed:
        raise ActionParseError(f"alignment must be one of: {', '.join(sorted(allowed))}")
    return normalized


def parse_action_payload(payload: dict[str, Any]) -> Action:
    action_type = payload.get("type")
    if not isinstance(action_type, str) or action_type not in SUPPORTED_ACTION_TYPES:
        supported = ", ".join(sorted(SUPPORTED_ACTION_TYPES))
        raise ActionParseError(f"type must be one of: {supported}")

    reason = payload.get("reason")
    if reason is not None and not isinstance(reason, str):
        raise ActionParseError("reason must be a string when provided")

    x = _optional_int(payload.get("x"), "x")
    y = _optional_int(payload.get("y"), "y")
    _validate_coordinate_fields(action_type, x, y)

    if action_type == "move_to" and (x is None or y is None):
        raise ActionParseError("move_to requires x and y")
    if action_type == "click" and (x is None or y is None):
        raise ActionParseError("click requires x and y")

    return Action(
        type=action_type,
        reason=reason.strip() if isinstance(reason, str) else None,
        x=x,
        y=y,
        delta_x=_optional_int(payload.get("delta_x"), "delta_x"),
        delta_y=_optional_int(payload.get("delta_y"), "delta_y"),
        text=_optional_str(payload.get("text"), "text"),
        wait_ms=_optional_int(payload.get("wait_ms"), "wait_ms"),
        target_kind=_optional_target_kind(payload.get("target_kind")),
        alignment=_optional_alignment(payload.get("alignment")),
    )


def extract_json_object(text: str) -> dict[str, Any]:
    stripped = text.strip()
    if not stripped:
        raise ActionParseError("empty VLM response")

    try:
        parsed = json.loads(stripped)
        if isinstance(parsed, dict):
            return parsed
    except json.JSONDecodeError:
        pass

    fence_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", stripped, re.DOTALL)
    if fence_match:
        parsed = json.loads(fence_match.group(1))
        if isinstance(parsed, dict):
            return parsed

    brace_match = re.search(r"\{.*\}", stripped, re.DOTALL)
    if brace_match:
        parsed = json.loads(brace_match.group(0))
        if isinstance(parsed, dict):
            return parsed

    raise ActionParseError("VLM response did not contain a JSON object")
