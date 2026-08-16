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
# Max Manhattan distance (norm 0–1000) a hover move_to may stray from L1 fine.
# Larger jumps are treated as VLM re-estimates and snapped back to the refine point
# (Feishu run feishu-om_x100b672…: hover jumped 750→500 / logo, then force-clicked off-target).
HOVER_MAX_ANCHOR_NORM_DELTA = 120
# After click_current with no_visible_change, allow limited re-aim rounds (PIN keypad false "aligned").
MAX_MISSED_CLICK_RECOVERIES = 2
MISSED_CLICK_RECOVERY_PASSES = 3
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
    """Last-resort L2: click after runner has snapped to L1 fine (see loop)."""
    reason = action.reason or "Confirming click at the L1 refine point."
    return Action(
        type="click_current",
        reason=f"{prefix} {reason}".strip(),
        alignment="adjusted",
        target_kind=action.target_kind,
    )


def l1_snap_before_adjusted_click(pending_click: Action) -> Action:
    """Move pointer back to L1 fine before an adjusted click_current."""
    assert pending_click.x is not None and pending_click.y is not None
    return Action(
        type="move_to",
        x=pending_click.x,
        y=pending_click.y,
        reason="UVG L2: snap to L1 fine before adjusted click",
        target_kind=pending_click.target_kind,
    )


def clamp_hover_alignment_action(
    action: Action,
    *,
    anchor_x: int,
    anchor_y: int,
    max_delta: int = HOVER_MAX_ANCHOR_NORM_DELTA,
) -> Action:
    """Keep hover move_to / move_by_delta near L1 fine; reject runaway re-points."""
    if action.type == "move_to":
        if action.x is None or action.y is None:
            return action
        dist = abs(action.x - anchor_x) + abs(action.y - anchor_y)
        if dist <= max_delta:
            return action
        original = action.reason or "hover move_to"
        return Action(
            type="move_to",
            x=anchor_x,
            y=anchor_y,
            reason=(
                f"UVG L2 clamp: hover move_to {dist} norm from L1 fine "
                f"(>{max_delta}); returning to refine point. Original: {original}"
            ),
            target_kind=action.target_kind,
        )

    if action.type == "move_by_delta":
        dx = int(action.delta_x or 0)
        dy = int(action.delta_y or 0)
        # move_by_delta is in pixels; approximate with a generous pixel budget (~12% of 1000-grid).
        max_px = max_delta
        mag = abs(dx) + abs(dy)
        if mag <= max_px:
            return action
        scale = max_px / mag
        original = action.reason or "hover move_by_delta"
        return Action(
            type="move_by_delta",
            delta_x=int(round(dx * scale)),
            delta_y=int(round(dy * scale)),
            reason=(
                f"UVG L2 clamp: hover delta {mag}px capped to {max_px}px. "
                f"Original: {original}"
            ),
            target_kind=action.target_kind,
        )

    return action


def should_force_hover_click(
    *,
    pass_index: int,
    passes: list[dict[str, Any]],
    hover_action: Action,
    max_pass_index: int = MAX_HOVER_ALIGNMENT_PASSES,
) -> bool:
    if hover_action.type not in HOVER_ALIGNMENT_ACTION_TYPES:
        return False
    if hover_action.type == "wait":
        return False
    if pass_index >= max_pass_index:
        return True
    return hover_adjustment_stalled(passes)


def should_recover_missed_click(
    *,
    verification: dict[str, Any] | None,
    missed_recoveries: int,
    max_recoveries: int = MAX_MISSED_CLICK_RECOVERIES,
) -> bool:
    """True when post-click telemetry shows no change and recovery budget remains."""
    if missed_recoveries >= max_recoveries:
        return False
    if not verification or not verification.get("applied"):
        return False
    return verification.get("outcome") == "no_visible_change"


def append_missed_click_history(
    maker: Any,
    *,
    step_index: int,
    recovery_index: int,
    pending_click: Action,
) -> None:
    """Tell the VLM the last click did not change the UI (e.g. PIN dots still empty)."""
    history = getattr(maker, "_history", None)
    if not isinstance(history, list):
        return
    target = pending_click.reason or "intended control"
    history.append(
        {
            "step": f"{step_index}:verify-miss-{recovery_index}",
            "action": {
                "type": "verification",
                "reason": (
                    f"Post-click verification: no_visible_change after click_current "
                    f"(recovery {recovery_index}/{MAX_MISSED_CLICK_RECOVERIES}). "
                    f"Do not assume progress (PIN/password dots, toggles, navigation). "
                    f"Re-aim the marker onto the center of: {target}"
                ),
            },
        }
    )


def derive_hover_alignment(
    *,
    pass_count: int,
    final_action_type: str,
    vlm_alignment: str | None = None,
    verification_outcome: str | None = None,
) -> str | None:
    """Derive hover alignment outcome for trace (G2)."""
    if verification_outcome == "no_visible_change" and final_action_type == "click_current":
        return "clicked_off_target"
    if vlm_alignment in HOVER_ALIGNMENT_OUTCOMES:
        return vlm_alignment
    if final_action_type == "click_current":
        return "aligned" if pass_count <= 1 else "adjusted"
    if final_action_type in HOVER_ALIGNMENT_ACTION_TYPES:
        return "unresolved"
    return None
