from __future__ import annotations

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
