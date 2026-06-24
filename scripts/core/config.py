from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

SUPPORTED_TARGETS = frozenset({"figma", "web"})
DEFAULT_MAX_STEPS = 10
DEFAULT_TIMEOUT_SECONDS = 180


@dataclass(frozen=True)
class TargetConfig:
    target: str
    url: str
    persona: str
    goal: str
    output_dir: Path
    max_steps: int
    timeout_seconds: int


class ConfigError(ValueError):
    """Raised when CLI or skill inputs fail validation."""


def _require_non_empty(value: str | None, field_name: str) -> str:
    if value is None or not value.strip():
        raise ConfigError(f"{field_name} is required")
    return value.strip()


def _validate_url(url: str) -> str:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ConfigError("url must be an absolute http or https URL")
    return url


def _validate_target(target: str) -> str:
    normalized = target.strip().lower()
    if normalized not in SUPPORTED_TARGETS:
        supported = ", ".join(sorted(SUPPORTED_TARGETS))
        raise ConfigError(f"target must be one of: {supported}")
    return normalized


def _validate_positive_int(value: int, field_name: str) -> int:
    if value <= 0:
        raise ConfigError(f"{field_name} must be a positive integer")
    return value


def build_target_config(
    *,
    target: str | None,
    url: str | None,
    persona: str | None,
    goal: str | None,
    output_dir: str | None,
    max_steps: int = DEFAULT_MAX_STEPS,
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
) -> TargetConfig:
    return TargetConfig(
        target=_validate_target(_require_non_empty(target, "target")),
        url=_validate_url(_require_non_empty(url, "url")),
        persona=_require_non_empty(persona, "persona"),
        goal=_require_non_empty(goal, "goal"),
        output_dir=Path(_require_non_empty(output_dir, "output_dir")),
        max_steps=_validate_positive_int(max_steps, "max_steps"),
        timeout_seconds=_validate_positive_int(timeout_seconds, "timeout_seconds"),
    )
