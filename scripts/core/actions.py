from __future__ import annotations

from dataclasses import dataclass
from typing import Any

TERMINAL_ACTIONS = frozenset({"done", "blocked", "max_steps", "timeout"})


@dataclass(frozen=True)
class Action:
    type: str
    reason: str | None = None

    def to_dict(self) -> dict[str, Any]:
        payload = {"type": self.type}
        if self.reason is not None:
            payload["reason"] = self.reason
        return payload


def is_terminal_action(action: Action) -> bool:
    return action.type in TERMINAL_ACTIONS
