from __future__ import annotations

from typing import Any

from core.actions import Action

HOVER_ALLOWED_ACTION_TYPES = frozenset(
    {
        "click_current",
        "move_to",
        "move_by_delta",
        "wait",
        "done",
        "blocked",
    }
)
HOVER_ALIGNMENT_ACTION_TYPES = frozenset({"move_to", "move_by_delta", "wait"})
MAX_HOVER_ALIGNMENT_PASSES = 5
HOVER_STALL_MIN_ADJUSTMENTS = 3
HOVER_STALL_MAX_NORM_DELTA = 15
HOVER_TARGET_KINDS = frozenset({"text", "icon", "composite", "button"})
HOVER_ALIGNMENT_OUTCOMES = frozenset({"aligned", "adjusted", "clicked_off_target", "unresolved"})


def action_triggers_hover(action: Action) -> bool:
    """Return True when the loop should capture hover feedback before clicking."""
    return action.type == "click" and action.x is not None and action.y is not None


def validate_hover_action(action: Action) -> None:
    if action.type not in HOVER_ALLOWED_ACTION_TYPES:
        allowed = ", ".join(sorted(HOVER_ALLOWED_ACTION_TYPES))
        raise ValueError(f"hover phase action must be one of: {allowed}")
    if action.type == "click":
        raise ValueError("use click_current after hover feedback, not click with coordinates")


def alignment_exhausted_blocked_action(
    *,
    passes: int,
    last_reason: str | None,
) -> Action:
    detail = last_reason or "pointer not aligned on target"
    return Action(
        type="blocked",
        reason=(
            f"UVG alignment exhausted after {passes} hover passes without click: {detail}"
        ),
    )


def _alignment_pass_coords(passes: list[dict[str, Any]]) -> list[tuple[int, int]]:
    coords: list[tuple[int, int]] = []
    for entry in passes:
        action = entry.get("decision", {}).get("action", {})
        if action.get("type") != "move_to":
            continue
        x, y = action.get("x"), action.get("y")
        if x is not None and y is not None:
            coords.append((int(x), int(y)))
    return coords


def hover_adjustment_stalled(
    passes: list[dict[str, Any]],
    *,
    min_adjustments: int = HOVER_STALL_MIN_ADJUSTMENTS,
    max_norm_delta: int = HOVER_STALL_MAX_NORM_DELTA,
) -> bool:
    """True when recent hover move_to targets barely change or oscillate."""
    coords = _alignment_pass_coords(passes)
    if len(coords) < min_adjustments:
        return False
    if len(coords) >= 3 and coords[-1] == coords[-3]:
        return True
    x0, y0 = coords[-1]
    x1, y1 = coords[-2]
    return abs(x1 - x0) + abs(y1 - y0) <= max_norm_delta


def coerce_hover_to_click(action: Action, *, prefix: str) -> Action:
    """Last-resort L2: click at pointer when micro-adjustments are not converging."""
    reason = action.reason or "Confirming click at the marked pointer."
    return Action(
        type="click_current",
        reason=f"{prefix} {reason}".strip(),
        alignment="adjusted",
        target_kind=action.target_kind,
    )


def should_force_hover_click(
    *,
    pass_index: int,
    passes: list[dict[str, Any]],
    hover_action: Action,
) -> bool:
    if hover_action.type not in HOVER_ALIGNMENT_ACTION_TYPES:
        return False
    if hover_action.type == "wait":
        return False
    if pass_index >= MAX_HOVER_ALIGNMENT_PASSES:
        return True
    return hover_adjustment_stalled(passes)


def derive_hover_alignment(
    *,
    pass_count: int,
    final_action_type: str,
    vlm_alignment: str | None = None,
) -> str | None:
    """Derive hover alignment outcome for trace (G2)."""
    if vlm_alignment in HOVER_ALIGNMENT_OUTCOMES:
        return vlm_alignment
    if final_action_type == "click_current":
        return "aligned" if pass_count <= 1 else "adjusted"
    if final_action_type in HOVER_ALIGNMENT_ACTION_TYPES:
        return "unresolved"
    return None
