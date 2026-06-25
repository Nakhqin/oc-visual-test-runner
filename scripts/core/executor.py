from __future__ import annotations

import time
from typing import Any

from adapters.browser import BrowserPlatformAdapter
from core.actions import Action

DEFAULT_SCROLL_DELTA_Y = 400
DEFAULT_WAIT_MS = 500


class ActionExecutionError(RuntimeError):
    """Raised when an action cannot be executed."""


def _execution_result(
    *,
    success: bool,
    action_type: str,
    error: str | None = None,
    page_url: str | None = None,
    cursor: dict[str, int] | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "success": success,
        "action": action_type,
        "error": error,
    }
    if page_url is not None:
        payload["page_url_after"] = page_url
    if cursor is not None:
        payload["cursor"] = cursor
    return payload


def execute_action(adapter: BrowserPlatformAdapter, action: Action) -> dict[str, Any]:
    """Execute a non-terminal action via the browser adapter."""
    try:
        if action.type == "move_to":
            if action.x is None or action.y is None:
                raise ActionExecutionError("move_to requires x and y")
            adapter.move_to(action.x, action.y)
        elif action.type == "move_by_delta":
            if action.delta_x is None or action.delta_y is None:
                raise ActionExecutionError("move_by_delta requires delta_x and delta_y")
            adapter.move_by_delta(action.delta_x, action.delta_y)
        elif action.type == "click":
            if action.x is None or action.y is None:
                raise ActionExecutionError("click requires x and y")
            adapter.click(action.x, action.y)
        elif action.type == "click_current":
            adapter.click_current()
        elif action.type == "scroll":
            adapter.scroll(action.delta_y if action.delta_y is not None else DEFAULT_SCROLL_DELTA_Y)
        elif action.type == "wait":
            adapter.wait(action.wait_ms if action.wait_ms is not None else DEFAULT_WAIT_MS)
        elif action.type == "type":
            if not action.text:
                raise ActionExecutionError("type requires text")
            adapter.type_text(action.text)
        else:
            raise ActionExecutionError(f"unsupported executable action: {action.type}")
    except ActionExecutionError as exc:
        return _execution_result(
            success=False,
            action_type=action.type,
            error=str(exc),
            page_url=adapter.page.url,
            cursor=adapter.cursor_position,
        )
    except Exception as exc:
        return _execution_result(
            success=False,
            action_type=action.type,
            error=f"browser execution failed: {exc}",
            page_url=adapter.page.url,
            cursor=adapter.cursor_position,
        )

    return _execution_result(
        success=True,
        action_type=action.type,
        page_url=adapter.page.url,
        cursor=adapter.cursor_position,
    )
