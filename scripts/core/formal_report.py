"""Phase 4 formal reports: ux_report.md and index.html."""

from __future__ import annotations

import html
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from core.config import TargetConfig
from core.report import (
    PERSONA_REPORT_FILENAME,
    collect_evidence_paths,
    derive_optional_findings,
    terminal_reason_from_trace,
    verification_stats,
)

UX_REPORT_FILENAME = "ux_report.md"
INDEX_HTML_FILENAME = "index.html"


@dataclass(frozen=True)
class FormalReportResult:
    ux_report_path: Path
    index_html_path: Path


def _viewport_from_trace(steps: list[dict[str, Any]]) -> tuple[int | None, int | None]:
    if not steps:
        return None, None
    observation = steps[0].get("observation", {})
    return observation.get("viewport_width"), observation.get("viewport_height")


def _action_summary(action: dict[str, Any]) -> str:
    action_type = action.get("type", "unknown")
    if action_type == "click":
        return f"`click` at ({action.get('x')}, {action.get('y')})"
    if action_type == "move_to":
        return f"`move_to` ({action.get('x')}, {action.get('y')})"
    if action_type == "move_by_delta":
        return f"`move_by_delta` ({action.get('delta_x')}, {action.get('delta_y')})"
    if action_type == "scroll":
        return f"`scroll` delta_y={action.get('delta_y')}"
    if action_type == "wait":
        return f"`wait` {action.get('wait_ms')}ms"
    if action_type == "type":
        return f"`type` {action.get('text')!r}"
    return f"`{action_type}`"


def _verification_summary(verification: dict[str, Any] | None) -> str | None:
    if not verification or not verification.get("applied"):
        return None
    outcome = verification.get("outcome", "unknown")
    retry_count = verification.get("retry_count", 0)
    hint = verification.get("interaction_hint")
    parts = [f"outcome={outcome}", f"retries={retry_count}"]
    if hint:
        parts.append(f"hint={hint}")
    return ", ".join(parts)


def _recommendations(
    *,
    terminal_state: str,
    classifications: list[str],
) -> list[str]:
    recommendations: list[str] = []
    if "system-runtime issue" in classifications:
        recommendations.append("Re-run when Gemini API or network conditions improve.")
    if terminal_state == "max_steps":
        recommendations.append("Increase `max_steps` if the persona needs more iterations to reach the goal.")
    if terminal_state == "timeout":
        recommendations.append("Increase `timeout_seconds` or simplify the goal for long-loading targets.")
    if not classifications and terminal_state in {"blocked", "max_steps", "timeout"}:
        recommendations.append(
            "Review the journey and evidence before promoting observations to confirmed UX defects."
        )
    if not recommendations:
        recommendations.append(
            "Review screenshots, recording, and persona_report.md alongside this formal report."
        )
    return recommendations


def _journey_markdown(steps: list[dict[str, Any]]) -> str:
    lines: list[str] = ["## Journey Timeline", ""]
    if not steps:
        lines.append("_No steps recorded._")
        return "\n".join(lines)

    for step in steps:
        step_index = step.get("step")
        phase = step.get("observation", {}).get("phase", "observe")
        action = step.get("decision", {}).get("action", {})
        source = step.get("decision", {}).get("source", "unknown")
        reason = action.get("reason") or "(no reason recorded)"
        screenshot = step.get("observation", {}).get("screenshot")

        lines.append(f"### Step {step_index} ({phase})")
        lines.append("")
        lines.append(f"- **Action:** {_action_summary(action)}")
        lines.append(f"- **Reason:** {reason}")
        lines.append(f"- **Decision source:** `{source}`")
        if screenshot:
            lines.append(f"- **Screenshot:** ![step {step_index}]({screenshot})")

        hover = step.get("hover")
        if isinstance(hover, dict):
            hover_action = hover.get("decision", {}).get("action", {})
            hover_reason = hover_action.get("reason") or "(no reason recorded)"
            hover_source = hover.get("decision", {}).get("source", source)
            hover_shot = hover.get("observation", {}).get("screenshot")
            lines.append(f"- **Hover action:** {_action_summary(hover_action)}")
            lines.append(f"- **Hover reason:** {hover_reason}")
            lines.append(f"- **Hover decision source:** `{hover_source}`")
            if hover_shot:
                lines.append(f"- **Hover screenshot:** ![step {step_index} hover]({hover_shot})")
            hover_execution = hover.get("execution")
            if isinstance(hover_execution, dict):
                summary = _verification_summary(hover_execution.get("verification"))
                if summary:
                    lines.append(f"- **Post-click verification:** {summary}")

        execution = step.get("execution")
        if isinstance(execution, dict) and not isinstance(hover, dict):
            summary = _verification_summary(execution.get("verification"))
            if summary:
                lines.append(f"- **Post-click verification:** {summary}")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def build_ux_report_md(
    config: TargetConfig,
    *,
    trace_payload: dict[str, Any],
    ux_result: dict[str, Any],
    decision_source: str,
) -> str:
    steps = trace_payload.get("steps", [])
    terminal_state = ux_result.get("terminal_state", "unknown")
    summary = ux_result.get("summary", "")
    main_finding = ux_result.get("main_finding", "")
    classifications = ux_result.get("classifications", [])
    limits = ux_result.get("limits", {})
    viewport_w, viewport_h = _viewport_from_trace(steps)
    terminal_reason, _ = terminal_reason_from_trace(steps)
    stats = verification_stats(steps)
    optional_findings = derive_optional_findings(
        terminal_state=terminal_state,
        main_finding=main_finding,
        classifications=classifications,
    )
    evidence_paths = collect_evidence_paths(config.output_dir, ux_result, steps)
    recommendations = _recommendations(
        terminal_state=terminal_state,
        classifications=classifications,
    )

    lines = [
        "# UX Visual Test Report",
        "",
        "## Summary",
        "",
        f"- **Outcome:** `{terminal_state}`",
        f"- **Summary:** {summary}",
        f"- **Main finding:** {main_finding}",
        f"- **Classifications:** {classifications or '(none)'}",
        "",
        "## Test Setup",
        "",
        f"- **Target:** `{config.target}`",
        f"- **URL:** {config.url}",
        f"- **Persona:** {config.persona}",
        f"- **Goal:** {config.goal}",
        f"- **Decision source:** `{decision_source}`",
        f"- **Viewport:** {viewport_w}×{viewport_h}" if viewport_w and viewport_h else "- **Viewport:** (unknown)",
        f"- **Limits:** max_steps={limits.get('max_steps')}, timeout_seconds={limits.get('timeout_seconds')}, steps_taken={limits.get('steps_taken')}",
        "",
        "## Final Outcome",
        "",
    ]
    if terminal_reason:
        lines.append(f"- **Terminal reason (from trace):** {terminal_reason}")
    else:
        lines.append(f"- **Terminal reason (from trace):** (none — ended with `{terminal_state}`)")
    lines.extend(["", _journey_markdown(steps), ""])
    lines.extend(
        [
            "## Post-Click Verification Summary",
            "",
            f"- visible_change: {stats.get('visible_change', 0)}",
            f"- no_visible_change: {stats.get('no_visible_change', 0)}",
            f"- execution_failed: {stats.get('execution_failed', 0)}",
            "",
            "_Verification is runner telemetry; it does not automatically classify UX defects._",
            "",
            "## Findings & Classification",
            "",
        ]
    )
    if optional_findings:
        for finding in optional_findings:
            lines.append(
                f"- **{finding['tag']}** — {finding['criteria']}; evidence: {finding['evidence']}; "
                f"{finding['note']}"
            )
    else:
        lines.append("No optional findings tagged under explicit Phase 3/4 criteria.")
    lines.extend(["", "## Evidence", ""])
    for path in evidence_paths:
        if path.endswith(".png"):
            lines.append(f"- ![evidence]({path})")
        else:
            lines.append(f"- `{path}`")
    lines.extend(["", "## Recommendations", ""])
    for rec in recommendations:
        lines.append(f"- {rec}")
    lines.extend(
        [
            "",
            "## Related Reports",
            "",
            f"- Persona narrative: `{PERSONA_REPORT_FILENAME}`",
            f"- Structured result: `ux_result.json`",
            f"- Full trace: `action_trace.json`",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def _html_section(title: str, body_html: str) -> str:
    return f"<section><h2>{html.escape(title)}</h2>{body_html}</section>"


def _journey_html(steps: list[dict[str, Any]]) -> str:
    if not steps:
        return "<p><em>No steps recorded.</em></p>"

    blocks: list[str] = []
    for step in steps:
        step_index = step.get("step")
        phase = step.get("observation", {}).get("phase", "observe")
        action = step.get("decision", {}).get("action", {})
        source = step.get("decision", {}).get("source", "unknown")
        reason = html.escape(action.get("reason") or "(no reason recorded)")
        screenshot = step.get("observation", {}).get("screenshot")

        parts = [
            f"<h3>Step {step_index} ({html.escape(phase)})</h3>",
            "<ul>",
            f"<li><strong>Action:</strong> {html.escape(_action_summary(action))}</li>",
            f"<li><strong>Reason:</strong> {reason}</li>",
            f"<li><strong>Decision source:</strong> <code>{html.escape(source)}</code></li>",
        ]
        if screenshot:
            parts.append(
                f'<li><strong>Screenshot:</strong><br><img src="{html.escape(screenshot)}" alt="step {step_index}"></li>'
            )

        hover = step.get("hover")
        if isinstance(hover, dict):
            hover_action = hover.get("decision", {}).get("action", {})
            hover_reason = html.escape(hover_action.get("reason") or "(no reason recorded)")
            hover_shot = hover.get("observation", {}).get("screenshot")
            parts.append(f"<li><strong>Hover action:</strong> {html.escape(_action_summary(hover_action))}</li>")
            parts.append(f"<li><strong>Hover reason:</strong> {hover_reason}</li>")
            if hover_shot:
                parts.append(
                    f'<li><strong>Hover screenshot:</strong><br>'
                    f'<img src="{html.escape(hover_shot)}" alt="step {step_index} hover"></li>'
                )
            hover_execution = hover.get("execution")
            if isinstance(hover_execution, dict):
                summary = _verification_summary(hover_execution.get("verification"))
                if summary:
                    parts.append(f"<li><strong>Post-click verification:</strong> {html.escape(summary)}</li>")

        execution = step.get("execution")
        if isinstance(execution, dict) and not isinstance(hover, dict):
            summary = _verification_summary(execution.get("verification"))
            if summary:
                parts.append(f"<li><strong>Post-click verification:</strong> {html.escape(summary)}</li>")

        parts.append("</ul>")
        blocks.append("\n".join(parts))
    return "\n".join(blocks)


def build_index_html(
    config: TargetConfig,
    *,
    trace_payload: dict[str, Any],
    ux_result: dict[str, Any],
    decision_source: str,
) -> str:
    steps = trace_payload.get("steps", [])
    terminal_state = ux_result.get("terminal_state", "unknown")
    summary = html.escape(ux_result.get("summary", ""))
    main_finding = html.escape(ux_result.get("main_finding", ""))
    classifications = ux_result.get("classifications", [])
    limits = ux_result.get("limits", {})
    viewport_w, viewport_h = _viewport_from_trace(steps)
    terminal_reason, _ = terminal_reason_from_trace(steps)
    stats = verification_stats(steps)
    optional_findings = derive_optional_findings(
        terminal_state=terminal_state,
        main_finding=ux_result.get("main_finding", ""),
        classifications=classifications,
    )
    recording = ux_result.get("artifacts", {}).get("recording")
    recommendations = _recommendations(
        terminal_state=terminal_state,
        classifications=classifications,
    )

    findings_html = "<ul>"
    if optional_findings:
        for finding in optional_findings:
            findings_html += (
                f"<li><strong>{html.escape(finding['tag'])}</strong> — "
                f"{html.escape(finding['criteria'])}; evidence: {html.escape(str(finding['evidence']))}; "
                f"{html.escape(finding['note'])}</li>"
            )
    else:
        findings_html += "<li>No optional findings tagged under explicit Phase 3/4 criteria.</li>"
    findings_html += "</ul>"

    rec_html = "".join(f"<li>{html.escape(rec)}</li>" for rec in recommendations)

    recording_html = ""
    if recording:
        recording_html = (
            f'<section><h2>Recording</h2><video controls width="960" src="{html.escape(recording)}"></video></section>'
        )

    body = "\n".join(
        [
            _html_section(
                "Summary",
                "<ul>"
                f"<li><strong>Outcome:</strong> <code>{html.escape(terminal_state)}</code></li>"
                f"<li><strong>Summary:</strong> {summary}</li>"
                f"<li><strong>Main finding:</strong> {main_finding}</li>"
                f"<li><strong>Classifications:</strong> {html.escape(str(classifications or '(none)'))}</li>"
                "</ul>",
            ),
            _html_section(
                "Test Setup",
                "<ul>"
                f"<li><strong>Target:</strong> <code>{html.escape(config.target)}</code></li>"
                f"<li><strong>URL:</strong> <a href=\"{html.escape(config.url)}\">{html.escape(config.url)}</a></li>"
                f"<li><strong>Persona:</strong> {html.escape(config.persona)}</li>"
                f"<li><strong>Goal:</strong> {html.escape(config.goal)}</li>"
                f"<li><strong>Decision source:</strong> <code>{html.escape(decision_source)}</code></li>"
                f"<li><strong>Viewport:</strong> {viewport_w}×{viewport_h}</li>"
                f"<li><strong>Limits:</strong> max_steps={limits.get('max_steps')}, "
                f"timeout_seconds={limits.get('timeout_seconds')}, steps_taken={limits.get('steps_taken')}</li>"
                "</ul>",
            ),
            _html_section(
                "Final Outcome",
                f"<p><strong>Terminal reason (from trace):</strong> "
                f"{html.escape(terminal_reason or f'(none — ended with {terminal_state})')}</p>",
            ),
            _html_section("Journey Timeline", _journey_html(steps)),
            _html_section(
                "Post-Click Verification Summary",
                "<ul>"
                f"<li>visible_change: {stats.get('visible_change', 0)}</li>"
                f"<li>no_visible_change: {stats.get('no_visible_change', 0)}</li>"
                f"<li>execution_failed: {stats.get('execution_failed', 0)}</li>"
                "</ul>"
                "<p><em>Verification is runner telemetry; it does not automatically classify UX defects.</em></p>",
            ),
            _html_section("Findings & Classification", findings_html),
            recording_html,
            _html_section("Recommendations", f"<ul>{rec_html}</ul>"),
            _html_section(
                "Related Reports",
                "<ul>"
                f'<li><a href="{html.escape(PERSONA_REPORT_FILENAME)}">persona_report.md</a></li>'
                f'<li><a href="ux_result.json">ux_result.json</a></li>'
                f'<li><a href="action_trace.json">action_trace.json</a></li>'
                f'<li><a href="{html.escape(UX_REPORT_FILENAME)}">ux_report.md</a></li>'
                "</ul>",
            ),
        ]
    )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>UX Visual Test Report — {html.escape(config.persona)}</title>
  <style>
    body {{ font-family: system-ui, sans-serif; line-height: 1.5; max-width: 960px; margin: 2rem auto; padding: 0 1rem; color: #1a1a1a; }}
    h1 {{ border-bottom: 2px solid #333; padding-bottom: 0.5rem; }}
    h2 {{ margin-top: 2rem; color: #333; }}
    img, video {{ max-width: 100%; border: 1px solid #ccc; border-radius: 4px; margin: 0.5rem 0; }}
    code {{ background: #f4f4f4; padding: 0.1rem 0.3rem; border-radius: 3px; }}
    section {{ margin-bottom: 1.5rem; }}
  </style>
</head>
<body>
  <h1>UX Visual Test Report</h1>
  <p><strong>Persona:</strong> {html.escape(config.persona)} · <strong>Goal:</strong> {html.escape(config.goal)}</p>
  {body}
</body>
</html>
"""


def build_skill_block(ux_result: dict[str, Any]) -> dict[str, Any]:
    persona = ux_result.get("persona", "")
    target = ux_result.get("target", "")
    terminal_state = ux_result.get("terminal_state", "unknown")
    main_finding = ux_result.get("main_finding", "")
    artifacts = ux_result.get("artifacts", {})
    return {
        "return_summary": (
            f"{persona} tested {target}: {terminal_state} — {main_finding}"
        ).strip(),
        "primary_report": INDEX_HTML_FILENAME,
        "markdown_report": UX_REPORT_FILENAME,
        "persona_report": artifacts.get("persona_report", PERSONA_REPORT_FILENAME),
        "result_json": "ux_result.json",
        "action_trace": "action_trace.json",
        "evidence": {
            "recording": artifacts.get("recording"),
            "screenshots_dir": artifacts.get("screenshots_dir", "screenshots/"),
        },
    }


def write_formal_reports(
    config: TargetConfig,
    *,
    trace_payload: dict[str, Any],
    ux_result: dict[str, Any],
    decision_source: str,
) -> FormalReportResult:
    ux_report_path = config.output_dir / UX_REPORT_FILENAME
    index_html_path = config.output_dir / INDEX_HTML_FILENAME
    ux_report_path.write_text(
        build_ux_report_md(
            config,
            trace_payload=trace_payload,
            ux_result=ux_result,
            decision_source=decision_source,
        ),
        encoding="utf-8",
    )
    index_html_path.write_text(
        build_index_html(
            config,
            trace_payload=trace_payload,
            ux_result=ux_result,
            decision_source=decision_source,
        ),
        encoding="utf-8",
    )

    updated = dict(ux_result)
    artifacts = dict(updated.get("artifacts", {}))
    artifacts["ux_report"] = UX_REPORT_FILENAME
    artifacts["index_html"] = INDEX_HTML_FILENAME
    updated["artifacts"] = artifacts
    updated["skill"] = build_skill_block(updated)
    (config.output_dir / "ux_result.json").write_text(
        json.dumps(updated, indent=2) + "\n",
        encoding="utf-8",
    )
    return FormalReportResult(
        ux_report_path=ux_report_path,
        index_html_path=index_html_path,
    )
