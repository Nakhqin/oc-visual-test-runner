from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from adapters.browser import BrowserPlatformAdapter
from core.actions import Action
from core.executor import execute_action

DEFAULT_CLICK_VERIFY_MAX_RETRIES = 1
DEFAULT_POST_CLICK_VERIFY_WAIT_MS = 500
DEFAULT_IMAGE_DIFF_RATIO_THRESHOLD = 0.01
ENV_CLICK_VERIFY_MAX_RETRIES = "CLICK_VERIFY_MAX_RETRIES"
ENV_POST_CLICK_VERIFY_WAIT_MS = "CLICK_VERIFY_POST_WAIT_MS"
ENV_IMAGE_DIFF_RATIO_THRESHOLD = "CLICK_VERIFY_IMAGE_DIFF_RATIO_THRESHOLD"

VERIFICATION_NOTE = (
    "Post-click verification is runner telemetry only; "
    "it does not automatically classify UX defects."
)

CLICK_VERIFIABLE_ACTION_TYPES = frozenset({"click", "click_current"})


def action_needs_post_click_verification(action: Action) -> bool:
    return action.type in CLICK_VERIFIABLE_ACTION_TYPES


def _env_int(name: str, default: int) -> int:
    raw = os.environ.get(name, "").strip()
    if not raw:
        return default
    try:
        return max(int(raw), 0)
    except ValueError:
        return default


def _env_float(name: str, default: float) -> float:
    raw = os.environ.get(name, "").strip()
    if not raw:
        return default
    try:
        return max(float(raw), 0.0)
    except ValueError:
        return default


def click_verify_max_retries() -> int:
    return _env_int(ENV_CLICK_VERIFY_MAX_RETRIES, DEFAULT_CLICK_VERIFY_MAX_RETRIES)


def post_click_verify_wait_ms() -> int:
    return _env_int(ENV_POST_CLICK_VERIFY_WAIT_MS, DEFAULT_POST_CLICK_VERIFY_WAIT_MS)


def image_diff_ratio_threshold() -> float:
    return _env_float(
        ENV_IMAGE_DIFF_RATIO_THRESHOLD,
        DEFAULT_IMAGE_DIFF_RATIO_THRESHOLD,
    )


def image_diff_ratio(path_before: Path, path_after: Path) -> float:
    """Return the fraction of pixels that differ between two screenshots."""
    from PIL import Image, ImageChops

    with Image.open(path_before) as before_raw, Image.open(path_after) as after_raw:
        if before_raw.size != after_raw.size:
            return 1.0
        before = before_raw.convert("RGB")
        after = after_raw.convert("RGB")
        diff = ImageChops.difference(before, after).convert("L")
        histogram = diff.histogram()
        changed_pixels = sum(histogram[level] for level in range(16, 256))
        total_pixels = before.size[0] * before.size[1]
        return changed_pixels / total_pixels if total_pixels else 0.0


def classify_interaction_hint(
    *,
    outcome: str,
    image_diff_ratio_value: float,
    retries_exhausted: bool,
) -> str | None:
    """Telemetry hint only — not an automatic UX classification."""
    if outcome != "no_visible_change":
        return None
    if image_diff_ratio_value == 0.0:
        return "possible_click_miss"
    if retries_exhausted:
        return "possible_ui_no_response"
    return "inconclusive_no_visible_change"


def build_verification_result(
    *,
    applied: bool,
    outcome: str,
    url_before: str | None = None,
    url_after: str | None = None,
    image_diff_ratio_value: float | None = None,
    image_diff_threshold: float | None = None,
    url_changed: bool | None = None,
    attempts: list[dict[str, Any]] | None = None,
    interaction_hint: str | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "applied": applied,
        "outcome": outcome,
        "note": VERIFICATION_NOTE,
    }
    if not applied:
        return payload

    payload["url_before"] = url_before
    payload["url_after"] = url_after
    payload["url_changed"] = url_changed
    payload["image_diff_ratio"] = image_diff_ratio_value
    payload["image_diff_threshold"] = image_diff_threshold
    if attempts is not None:
        payload["attempts"] = attempts
        payload["retry_count"] = max(len(attempts) - 1, 0)
    if interaction_hint is not None:
        payload["interaction_hint"] = interaction_hint
    return payload


def not_applicable_verification() -> dict[str, Any]:
    return build_verification_result(applied=False, outcome="not_applicable")


def evaluate_post_click_outcome(
    *,
    execution: dict[str, Any],
    url_before: str,
    url_after: str,
    before_path: Path,
    after_path: Path,
    diff_threshold: float,
) -> tuple[str, float, bool]:
    if not execution.get("success", False):
        return "execution_failed", 0.0, False

    url_changed = url_before != url_after
    diff_ratio = image_diff_ratio(before_path, after_path)
    if url_changed or diff_ratio >= diff_threshold:
        return "visible_change", diff_ratio, url_changed
    return "no_visible_change", diff_ratio, url_changed


def execute_with_verification(
    adapter: BrowserPlatformAdapter,
    action: Action,
    *,
    output_dir: Path,
    step_index: int,
    max_retries: int | None = None,
) -> dict[str, Any]:
    """Execute click actions with bounded post-click verification and retry."""
    if not action_needs_post_click_verification(action):
        execution = execute_action(adapter, action)
        execution["verification"] = not_applicable_verification()
        return execution

    retries_allowed = click_verify_max_retries() if max_retries is None else max(0, max_retries)
    wait_ms = post_click_verify_wait_ms()
    diff_threshold = image_diff_ratio_threshold()
    verify_dir = output_dir / "screenshots" / "verify"
    verify_dir.mkdir(parents=True, exist_ok=True)

    attempts: list[dict[str, Any]] = []
    final_outcome = "no_visible_change"
    final_execution: dict[str, Any] | None = None
    final_url_before = ""
    final_url_after = ""
    final_diff_ratio = 0.0
    final_url_changed = False

    for attempt in range(retries_allowed + 1):
        before_path = verify_dir / f"step-{step_index:03d}-attempt-{attempt}-before.png"
        adapter.capture_page_snapshot(before_path)
        url_before = adapter.page.url

        execution = execute_action(adapter, action)
        adapter.wait(wait_ms)

        after_path = verify_dir / f"step-{step_index:03d}-attempt-{attempt}-after.png"
        adapter.capture_page_snapshot(after_path)
        url_after = adapter.page.url

        outcome, diff_ratio, url_changed = evaluate_post_click_outcome(
            execution=execution,
            url_before=url_before,
            url_after=url_after,
            before_path=before_path,
            after_path=after_path,
            diff_threshold=diff_threshold,
        )

        attempts.append(
            {
                "attempt": attempt + 1,
                "outcome": outcome,
                "url_before": url_before,
                "url_after": url_after,
                "url_changed": url_changed,
                "image_diff_ratio": round(diff_ratio, 6),
                "execution_success": execution.get("success", False),
                "before_screenshot": before_path.relative_to(output_dir).as_posix(),
                "after_screenshot": after_path.relative_to(output_dir).as_posix(),
            }
        )

        final_outcome = outcome
        final_execution = execution
        final_url_before = url_before
        final_url_after = url_after
        final_diff_ratio = diff_ratio
        final_url_changed = url_changed

        if outcome in {"visible_change", "execution_failed"}:
            break

    assert final_execution is not None
    retries_exhausted = len(attempts) >= retries_allowed + 1
    interaction_hint = classify_interaction_hint(
        outcome=final_outcome,
        image_diff_ratio_value=final_diff_ratio,
        retries_exhausted=retries_exhausted,
    )
    final_execution["verification"] = build_verification_result(
        applied=True,
        outcome=final_outcome,
        url_before=final_url_before,
        url_after=final_url_after,
        image_diff_ratio_value=round(final_diff_ratio, 6),
        image_diff_threshold=diff_threshold,
        url_changed=final_url_changed,
        attempts=attempts,
        interaction_hint=interaction_hint,
    )
    return final_execution
