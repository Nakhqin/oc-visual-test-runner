"""Phase 4.5: optional public report publish and run_id resolution."""

from __future__ import annotations

import json
import os
import re
import shutil
import sys
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from core.formal_report import INDEX_HTML_FILENAME

ENV_UX_REPORT_PUBLIC_DIR = "UX_REPORT_PUBLIC_DIR"
ENV_UX_REPORT_PUBLIC_BASE_URL = "UX_REPORT_PUBLIC_BASE_URL"
ENV_RUN_ID = "RUN_ID"

_RUN_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")


@dataclass(frozen=True)
class PublishConfig:
    public_dir: Path
    base_url: str


@dataclass(frozen=True)
class PublishFinalizeResult:
    run_id: str
    enabled: bool
    report_url: str | None = None
    report_base_url: str | None = None
    published_dir: Path | None = None


def generate_run_id() -> str:
    """Return ``{UTC_timestamp}-{short_uuid}`` (e.g. ``20260703-154812-a1b2c3d4``)."""
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    return f"{timestamp}-{uuid.uuid4().hex[:8]}"


def validate_run_id(run_id: str) -> str:
    normalized = run_id.strip()
    if not normalized:
        raise ValueError("run_id must not be empty")
    if not _RUN_ID_PATTERN.match(normalized):
        raise ValueError(
            "run_id must be 1–128 characters of letters, digits, '.', '_', or '-' "
            "and must not contain path separators"
        )
    return normalized


def resolve_run_id(explicit: str | None = None) -> str:
    """Resolve run id from CLI, ``RUN_ID`` env, or auto-generate."""
    candidate = (explicit or os.environ.get(ENV_RUN_ID, "")).strip()
    if candidate:
        return validate_run_id(candidate)
    return generate_run_id()


def publish_config_from_env() -> PublishConfig | None:
    public_dir_raw = os.environ.get(ENV_UX_REPORT_PUBLIC_DIR, "").strip()
    base_url_raw = os.environ.get(ENV_UX_REPORT_PUBLIC_BASE_URL, "").strip()

    if not public_dir_raw and not base_url_raw:
        return None
    if not public_dir_raw or not base_url_raw:
        print(
            "warning: report publish disabled — set both "
            f"{ENV_UX_REPORT_PUBLIC_DIR} and {ENV_UX_REPORT_PUBLIC_BASE_URL}",
            file=sys.stderr,
        )
        return None

    return PublishConfig(
        public_dir=Path(public_dir_raw),
        base_url=base_url_raw.rstrip("/"),
    )


def selected_report_publish_mode() -> str:
    return "enabled" if publish_config_from_env() is not None else "disabled"


def _atomic_copytree(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    staging = destination.parent / f".{destination.name}.tmp-{uuid.uuid4().hex[:8]}"
    if staging.exists():
        shutil.rmtree(staging)
    shutil.copytree(source, staging)
    if destination.exists():
        shutil.rmtree(destination)
    staging.rename(destination)


def publish_output_dir(
    output_dir: Path,
    *,
    run_id: str,
    config: PublishConfig,
) -> PublishFinalizeResult:
    """Copy the full output directory to the public publish root."""
    published_dir = config.public_dir / run_id
    _atomic_copytree(output_dir, published_dir)
    report_base_url = f"{config.base_url}/{run_id}"
    report_url = f"{report_base_url}/{INDEX_HTML_FILENAME}"
    return PublishFinalizeResult(
        run_id=run_id,
        enabled=True,
        report_url=report_url,
        report_base_url=report_base_url,
        published_dir=published_dir,
    )


def _load_ux_result(output_dir: Path) -> dict:
    ux_result_path = output_dir / "ux_result.json"
    return json.loads(ux_result_path.read_text(encoding="utf-8"))


def _write_ux_result(output_dir: Path, payload: dict) -> None:
    (output_dir / "ux_result.json").write_text(
        json.dumps(payload, indent=2) + "\n",
        encoding="utf-8",
    )


def _apply_run_id(output_dir: Path, run_id: str) -> None:
    payload = _load_ux_result(output_dir)
    payload["run_id"] = run_id
    _write_ux_result(output_dir, payload)


def _apply_publish_urls(output_dir: Path, result: PublishFinalizeResult) -> None:
    payload = _load_ux_result(output_dir)
    skill = dict(payload.get("skill", {}))
    skill["report_url"] = result.report_url
    skill["report_base_url"] = result.report_base_url
    payload["skill"] = skill
    payload["run_id"] = result.run_id
    _write_ux_result(output_dir, payload)

    if result.published_dir is not None:
        published_payload = dict(payload)
        (result.published_dir / "ux_result.json").write_text(
            json.dumps(published_payload, indent=2) + "\n",
            encoding="utf-8",
        )


def finalize_report_publish(
    output_dir: Path,
    *,
    run_id: str | None = None,
) -> PublishFinalizeResult:
    """Resolve run_id, optionally publish, and update ``ux_result.json``."""
    resolved_run_id = resolve_run_id(run_id)
    config = publish_config_from_env()
    if config is None:
        _apply_run_id(output_dir, resolved_run_id)
        return PublishFinalizeResult(run_id=resolved_run_id, enabled=False)

    result = publish_output_dir(output_dir, run_id=resolved_run_id, config=config)
    _apply_publish_urls(output_dir, result)
    return result
