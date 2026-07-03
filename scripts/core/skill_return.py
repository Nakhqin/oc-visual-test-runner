"""Format OpenClaw / Feishu user-facing replies from ux_result.json."""

from __future__ import annotations

from typing import Any


def _classifications_text(classifications: list[str] | None) -> str:
    if not classifications:
        return "(none)"
    return ", ".join(classifications)


def _public_url(skill: dict[str, Any], key: str, *, fallback_base: str | None, rel_path: str | None) -> str | None:
    explicit = skill.get(key)
    if explicit:
        return str(explicit)
    if fallback_base and rel_path:
        return f"{fallback_base.rstrip('/')}/{rel_path.lstrip('/')}"
    return None


def format_feishu_reply(ux_result: dict[str, Any]) -> str:
    """Return concise Feishu text per ``docs/OPENCLAW_INTEGRATION.md``."""
    skill = ux_result.get("skill", {})
    report_base = skill.get("report_base_url")
    artifacts = ux_result.get("artifacts", {})
    recording_rel = artifacts.get("recording")

    report_url = skill.get("report_url")
    recording_url = _public_url(
        skill,
        "recording_url",
        fallback_base=report_base,
        rel_path=recording_rel,
    )
    result_json_url = _public_url(
        skill,
        "result_json_url",
        fallback_base=report_base,
        rel_path="ux_result.json",
    )

    lines = [
        "UX visual test completed.",
        "",
        f"Target: {ux_result.get('target', 'unknown')}",
        f"Persona: {ux_result.get('persona', '')}",
        f"Goal: {ux_result.get('goal', '')}",
        f"Outcome: {ux_result.get('terminal_state', 'unknown')}",
        f"Main finding: {ux_result.get('main_finding', '')}",
        f"Classification: {_classifications_text(ux_result.get('classifications'))}",
    ]

    summary = skill.get("return_summary")
    if summary:
        lines.extend(["", f"Summary: {summary}"])

    lines.append("")
    if report_url:
        lines.append(f"Report: {report_url}")
    else:
        index_html = artifacts.get("index_html", "index.html")
        output_dir = ux_result.get("output_dir", "")
        local_report = f"{output_dir}/{index_html}" if output_dir else index_html
        lines.append(f"Report (local only): {local_report}")
        lines.append("Note: public report URL unavailable — publish env was not set.")

    if recording_url:
        lines.append(f"Recording: {recording_url}")
    elif recording_rel:
        lines.append(f"Recording (local): {recording_rel}")

    if result_json_url:
        lines.append(f"Result JSON: {result_json_url}")

    run_id = ux_result.get("run_id")
    if run_id:
        lines.append(f"Run id: {run_id}")

    return "\n".join(lines)


def format_feishu_error(
    *,
    message: str,
    run_id: str | None = None,
    detail: str | None = None,
) -> str:
    lines = [
        "UX visual test could not complete.",
        "",
        f"Reason: {message}",
    ]
    if run_id:
        lines.append(f"Run id: {run_id}")
    if detail:
        lines.append(f"Detail: {detail}")
    lines.extend(
        [
            "",
            "Please retry with a simpler goal or check runner logs on the VM.",
        ]
    )
    return "\n".join(lines)
