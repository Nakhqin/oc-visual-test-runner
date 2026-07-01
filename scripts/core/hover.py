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


def action_triggers_hover(action: Action) -> bool:
    """Return True when the loop should capture hover feedback before clicking."""
    return action.type == "click" and action.x is not None and action.y is not None


def validate_hover_action(action: Action) -> None:
    if action.type not in HOVER_ALLOWED_ACTION_TYPES:
        allowed = ", ".join(sorted(HOVER_ALLOWED_ACTION_TYPES))
        raise ValueError(f"hover phase action must be one of: {allowed}")
    if action.type == "click":
        raise ValueError("use click_current after hover feedback, not click with coordinates")
