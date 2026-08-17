"""Phase 4 formal reports: ux_report.md and index.html (User Testing Report outline)."""

from __future__ import annotations

import html
import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
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


def _format_report_date(created_at: str | None) -> str:
    if not created_at:
        return datetime.now(timezone.utc).strftime("%B %d, %Y")
    raw = created_at.strip()
    try:
        if raw.endswith("Z"):
            raw = raw[:-1] + "+00:00"
        dt = datetime.fromisoformat(raw)
        return dt.strftime("%B %d, %Y")
    except ValueError:
        return raw[:10] if len(raw) >= 10 else raw


def _step_verification_outcome(step: dict[str, Any]) -> str | None:
    hover = step.get("hover")
    if isinstance(hover, dict):
        execution = hover.get("execution")
        if isinstance(execution, dict):
            verification = execution.get("verification")
            if isinstance(verification, dict) and verification.get("applied"):
                outcome = verification.get("outcome")
                return str(outcome) if outcome else None
    execution = step.get("execution")
    if isinstance(execution, dict):
        verification = execution.get("verification")
        if isinstance(verification, dict) and verification.get("applied"):
            outcome = verification.get("outcome")
            return str(outcome) if outcome else None
    return None


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


def _executive_summary(
    *,
    config: TargetConfig,
    terminal_state: str,
    summary: str,
    main_finding: str,
    steps_taken: Any,
) -> str:
    parts = [
        (
            f"We ran a persona-based visual UX walkthrough on `{config.target}` "
            f"({config.persona}). Goal: {config.goal}"
        ),
        f"The run ended with `{terminal_state}` after {steps_taken} steps.",
    ]
    takeaway = (main_finding or summary or "").strip()
    if takeaway:
        parts.append(f"Biggest takeaway: {takeaway}")
    return " ".join(parts)


def _key_findings(
    *,
    steps: list[dict[str, Any]],
    terminal_state: str,
    main_finding: str,
    classifications: list[str],
    stats: dict[str, int],
    optional_findings: list[dict[str, str]],
) -> tuple[list[str], list[str]]:
    positives: list[str] = []
    pains: list[str] = []

    visible_steps: list[int] = []
    miss_steps: list[int] = []
    for step in steps:
        outcome = _step_verification_outcome(step)
        idx = step.get("step")
        if outcome == "visible_change" and isinstance(idx, int):
            visible_steps.append(idx)
        if outcome == "no_visible_change" and isinstance(idx, int):
            miss_steps.append(idx)

    if visible_steps:
        preview = ", ".join(str(i) for i in visible_steps[:8])
        more = "" if len(visible_steps) <= 8 else f" (+{len(visible_steps) - 8} more)"
        positives.append(
            f"**Forward progress:** {len(visible_steps)} click(s) produced a visible UI change "
            f"(steps {preview}{more})."
        )

    early_streak = 0
    for step in steps:
        if _step_verification_outcome(step) == "visible_change":
            early_streak += 1
        else:
            break
    if early_streak >= 2:
        positives.append(
            f"**Early flow clarity:** the first {early_streak} interactive steps advanced without stalling."
        )

    if terminal_state == "done":
        positives.append("**Goal completed:** the persona reached a `done` terminal state.")

    if not positives:
        positives.append(
            "No strong positives were auto-tagged; review the Journey Timeline for moments that felt smooth."
        )

    no_change = stats.get("no_visible_change", 0)
    if no_change:
        sample = ", ".join(str(i) for i in miss_steps[:8])
        more = "" if len(miss_steps) <= 8 else f" (+{len(miss_steps) - 8} more)"
        pains.append(
            f"**Unresponsive taps (telemetry):** {no_change} click(s) recorded `no_visible_change` "
            f"(steps {sample}{more}). "
            "_This is runner telemetry — not an automatic product UX defect._"
        )

    off_target = 0
    for step in steps:
        hover = step.get("hover")
        if isinstance(hover, dict) and hover.get("alignment") == "clicked_off_target":
            off_target += 1
    if off_target:
        pains.append(
            f"**Pointer alignment struggle:** {off_target} step(s) ended hover alignment as "
            "`clicked_off_target` after missed-click recovery."
        )

    if terminal_state in {"blocked", "max_steps", "timeout"} and main_finding:
        pains.append(f"**Run stopped (`{terminal_state}`):** {main_finding}")

    for finding in optional_findings:
        pains.append(
            f"**{finding['tag']}:** {finding['criteria']} "
            f"(evidence: {finding['evidence']}). {finding['note']}"
        )

    if classifications:
        pains.append(f"**Classifications:** {', '.join(classifications)}.")

    if not pains:
        pains.append("No major pain points were auto-tagged for this run.")

    return positives, pains


def _prioritized_recommendations(
    *,
    terminal_state: str,
    classifications: list[str],
    stats: dict[str, int],
) -> list[tuple[str, str]]:
    """Return (priority, text) pairs."""
    items: list[tuple[str, str]] = []
    if "system-runtime issue" in classifications:
        items.append(
            ("High Priority", "Re-run when Gemini API or network conditions improve.")
        )
    if stats.get("no_visible_change", 0) >= 3:
        items.append(
            (
                "High Priority",
                "Review Journey screenshots/recording for repeated `no_visible_change` taps "
                "(grounding miss vs product non-response) before filing UX bugs.",
            )
        )
    if terminal_state == "max_steps":
        items.append(
            (
                "Medium Priority",
                "Increase `max_steps` if the persona needs more iterations to reach the goal.",
            )
        )
    if terminal_state == "timeout":
        items.append(
            (
                "Medium Priority",
                "Increase `timeout_seconds` or simplify the goal for long-loading targets.",
            )
        )
    if terminal_state == "blocked":
        items.append(
            (
                "Medium Priority",
                "Inspect the final blocked step in the Journey Timeline and recording; "
                "confirm whether the blocker is product copy/flow or pointer accuracy.",
            )
        )
    if not items:
        items.append(
            (
                "Medium Priority",
                "Review screenshots, recording, and persona_report.md alongside this report.",
            )
        )
    return items


def _recommendations(
    *,
    terminal_state: str,
    classifications: list[str],
) -> list[str]:
    """Backward-compatible flat list (tests / callers)."""
    stats = {"no_visible_change": 0}
    return [
        f"**{priority}:** {text}"
        for priority, text in _prioritized_recommendations(
            terminal_state=terminal_state,
            classifications=classifications,
            stats=stats,
        )
    ]


def _md_inline_to_html(text: str) -> str:
    """Minimal **bold** and `code` after HTML escape for finding bullets."""
    escaped = html.escape(text)
    escaped = re.sub(r"`([^`]+)`", r"<code>\1</code>", escaped)
    escaped = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", escaped)
    escaped = re.sub(r"_([^_]+)_", r"<em>\1</em>", escaped)
    return escaped


def _journey_markdown(steps: list[dict[str, Any]]) -> str:
    lines: list[str] = []
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

        refine = step.get("refine")
        if isinstance(refine, dict):
            coarse = refine.get("coarse", {})
            fine = refine.get("fine", {})
            crop = refine.get("crop", {})
            lines.append(
                f"- **UVG refine:** {_action_summary(coarse)} → {_action_summary(fine)}"
            )
            crop_shot = crop.get("screenshot")
            if crop_shot:
                lines.append(f"- **Refine crop:** ![step {step_index} refine]({crop_shot})")

        hover = step.get("hover")
        if isinstance(hover, dict):
            hover_action = hover.get("decision", {}).get("action", {})
            hover_reason = hover_action.get("reason") or "(no reason recorded)"
            hover_source = hover.get("decision", {}).get("source", source)
            hover_shot = hover.get("observation", {}).get("screenshot")
            lines.append(f"- **Hover action:** {_action_summary(hover_action)}")
            lines.append(f"- **Hover reason:** {hover_reason}")
            lines.append(f"- **Hover decision source:** `{hover_source}`")
            if hover.get("alignment"):
                lines.append(f"- **Hover alignment:** `{hover.get('alignment')}`")
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
    report_date = _format_report_date(ux_result.get("created_at"))
    exec_summary = _executive_summary(
        config=config,
        terminal_state=terminal_state,
        summary=summary,
        main_finding=main_finding,
        steps_taken=limits.get("steps_taken"),
    )
    positives, pains = _key_findings(
        steps=steps,
        terminal_state=terminal_state,
        main_finding=main_finding,
        classifications=classifications,
        stats=stats,
        optional_findings=optional_findings,
    )
    rec_items = _prioritized_recommendations(
        terminal_state=terminal_state,
        classifications=classifications,
        stats=stats,
    )
    recording = ux_result.get("artifacts", {}).get("recording")
    screenshots = [p for p in evidence_paths if p.endswith(".png")]

    lines = [
        "## User Testing Report",
        "",
        f"**Date:** {report_date}",
        "",
        "### Test setup",
        "",
        f"- **Target:** `{config.target}`",
        f"- **URL:** {config.url}",
        f"- **Persona:** {config.persona}",
        f"- **Goal:** {config.goal}",
        f"- **Decision source:** `{decision_source}`",
        (
            f"- **Viewport:** {viewport_w}×{viewport_h}"
            if viewport_w and viewport_h
            else "- **Viewport:** (unknown)"
        ),
        (
            f"- **Limits:** max_steps={limits.get('max_steps')}, "
            f"timeout_seconds={limits.get('timeout_seconds')}, "
            f"steps_taken={limits.get('steps_taken')}"
        ),
        f"- **Outcome:** `{terminal_state}`",
        "",
        "### 1. Executive Summary",
        "",
        exec_summary,
        "",
    ]
    if terminal_reason:
        lines.extend(
            [
                f"_Terminal reason (from trace):_ {terminal_reason}",
                "",
            ]
        )

    lines.extend(
        [
            "### 2. Key Findings",
            "",
            "**What Worked Well (Positives):**",
            "",
        ]
    )
    for item in positives:
        lines.append(f"- {item}")
    lines.extend(["", "**Pain Points (Areas for Improvement):**", ""])
    for item in pains:
        lines.append(f"- {item}")
    lines.extend(
        [
            "",
            "_Verification counts (telemetry only):_ "
            f"visible_change={stats.get('visible_change', 0)}, "
            f"no_visible_change={stats.get('no_visible_change', 0)}, "
            f"execution_failed={stats.get('execution_failed', 0)}.",
            "",
            "### 3. Journey Timeline",
            "",
            _journey_markdown(steps).rstrip(),
            "",
            "### 4. Recommendations",
            "",
        ]
    )
    for priority, text in rec_items:
        lines.append(f"- **{priority}:** {text}")

    lines.extend(["", "### 5. Appendix", "", "**Video record**", ""])
    if recording:
        lines.append(f"- `{recording}`")
    else:
        lines.append("- _(no recording artifact)_")
    lines.extend(["", "**Screenshots**", ""])
    if screenshots:
        for path in screenshots[:40]:
            lines.append(f"- ![screenshot]({path})")
        if len(screenshots) > 40:
            lines.append(f"- _…and {len(screenshots) - 40} more under `screenshots/`_")
    else:
        lines.append("- _(no screenshots)_")
    lines.extend(
        [
            "",
            "**Related files**",
            "",
            f"- Persona narrative: `{PERSONA_REPORT_FILENAME}`",
            f"- Structured result: `ux_result.json`",
            f"- Full trace: `action_trace.json`",
            f"- Markdown twin: `{UX_REPORT_FILENAME}`",
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
                f'<li><strong>Screenshot:</strong><br>'
                f'<img src="{html.escape(screenshot)}" alt="step {step_index}"></li>'
            )

        refine = step.get("refine")
        if isinstance(refine, dict):
            coarse = refine.get("coarse", {})
            fine = refine.get("fine", {})
            crop = refine.get("crop", {})
            parts.append(
                "<li><strong>UVG refine:</strong> "
                f"{html.escape(_action_summary(coarse))} → "
                f"{html.escape(_action_summary(fine))}</li>"
            )
            crop_shot = crop.get("screenshot")
            if crop_shot:
                parts.append(
                    f'<li><strong>Refine crop:</strong><br>'
                    f'<img src="{html.escape(crop_shot)}" alt="step {step_index} refine"></li>'
                )

        hover = step.get("hover")
        if isinstance(hover, dict):
            hover_action = hover.get("decision", {}).get("action", {})
            hover_reason = html.escape(hover_action.get("reason") or "(no reason recorded)")
            hover_shot = hover.get("observation", {}).get("screenshot")
            parts.append(
                f"<li><strong>Hover action:</strong> {html.escape(_action_summary(hover_action))}</li>"
            )
            parts.append(f"<li><strong>Hover reason:</strong> {hover_reason}</li>")
            if hover.get("alignment"):
                parts.append(
                    f"<li><strong>Hover alignment:</strong> "
                    f"<code>{html.escape(str(hover.get('alignment')))}</code></li>"
                )
            if hover_shot:
                parts.append(
                    f'<li><strong>Hover screenshot:</strong><br>'
                    f'<img src="{html.escape(hover_shot)}" alt="step {step_index} hover"></li>'
                )
            hover_execution = hover.get("execution")
            if isinstance(hover_execution, dict):
                summary = _verification_summary(hover_execution.get("verification"))
                if summary:
                    parts.append(
                        f"<li><strong>Post-click verification:</strong> {html.escape(summary)}</li>"
                    )

        execution = step.get("execution")
        if isinstance(execution, dict) and not isinstance(hover, dict):
            summary = _verification_summary(execution.get("verification"))
            if summary:
                parts.append(
                    f"<li><strong>Post-click verification:</strong> {html.escape(summary)}</li>"
                )

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
    recording = ux_result.get("artifacts", {}).get("recording")
    evidence_paths = collect_evidence_paths(config.output_dir, ux_result, steps)
    screenshots = [p for p in evidence_paths if p.endswith(".png")]
    report_date = _format_report_date(ux_result.get("created_at"))
    exec_summary = _executive_summary(
        config=config,
        terminal_state=terminal_state,
        summary=summary,
        main_finding=main_finding,
        steps_taken=limits.get("steps_taken"),
    )
    positives, pains = _key_findings(
        steps=steps,
        terminal_state=terminal_state,
        main_finding=main_finding,
        classifications=classifications,
        stats=stats,
        optional_findings=optional_findings,
    )
    rec_items = _prioritized_recommendations(
        terminal_state=terminal_state,
        classifications=classifications,
        stats=stats,
    )

    positives_html = (
        "<ul>" + "".join(f"<li>{_md_inline_to_html(p)}</li>" for p in positives) + "</ul>"
    )
    pains_html = "<ul>" + "".join(f"<li>{_md_inline_to_html(p)}</li>" for p in pains) + "</ul>"
    rec_html = (
        "<ul>"
        + "".join(
            f"<li><strong>{html.escape(priority)}:</strong> {html.escape(text)}</li>"
            for priority, text in rec_items
        )
        + "</ul>"
    )

    recording_block = "<p><em>(no recording artifact)</em></p>"
    if recording:
        recording_block = (
            f'<video controls width="960" src="{html.escape(recording)}"></video>'
            f"<p><code>{html.escape(recording)}</code></p>"
        )

    shots_html = "<p><em>(no screenshots)</em></p>"
    if screenshots:
        imgs = []
        for path in screenshots[:40]:
            imgs.append(
                f'<figure><img src="{html.escape(path)}" alt="screenshot">'
                f"<figcaption><code>{html.escape(path)}</code></figcaption></figure>"
            )
        if len(screenshots) > 40:
            imgs.append(
                f"<p><em>…and {len(screenshots) - 40} more under screenshots/</em></p>"
            )
        shots_html = "\n".join(imgs)

    setup_html = (
        "<ul>"
        f"<li><strong>Target:</strong> <code>{html.escape(config.target)}</code></li>"
        f"<li><strong>URL:</strong> <a href=\"{html.escape(config.url)}\">{html.escape(config.url)}</a></li>"
        f"<li><strong>Persona:</strong> {html.escape(config.persona)}</li>"
        f"<li><strong>Goal:</strong> {html.escape(config.goal)}</li>"
        f"<li><strong>Decision source:</strong> <code>{html.escape(decision_source)}</code></li>"
        f"<li><strong>Viewport:</strong> {viewport_w}×{viewport_h}</li>"
        f"<li><strong>Limits:</strong> max_steps={html.escape(str(limits.get('max_steps')))}, "
        f"timeout_seconds={html.escape(str(limits.get('timeout_seconds')))}, "
        f"steps_taken={html.escape(str(limits.get('steps_taken')))}</li>"
        f"<li><strong>Outcome:</strong> <code>{html.escape(terminal_state)}</code></li>"
        "</ul>"
    )

    exec_extra = ""
    if terminal_reason:
        exec_extra = (
            f"<p><em>Terminal reason (from trace):</em> {html.escape(terminal_reason)}</p>"
        )

    body = "\n".join(
        [
            f"<p><strong>Date:</strong> {html.escape(report_date)}</p>",
            _html_section("Test setup", setup_html),
            _html_section(
                "1. Executive Summary",
                f"<p>{html.escape(exec_summary)}</p>{exec_extra}",
            ),
            _html_section(
                "2. Key Findings",
                "<h3>What Worked Well (Positives)</h3>"
                f"{positives_html}"
                "<h3>Pain Points (Areas for Improvement)</h3>"
                f"{pains_html}"
                "<p><em>Verification counts (telemetry only): "
                f"visible_change={stats.get('visible_change', 0)}, "
                f"no_visible_change={stats.get('no_visible_change', 0)}, "
                f"execution_failed={stats.get('execution_failed', 0)}.</em></p>",
            ),
            _html_section("3. Journey Timeline", _journey_html(steps)),
            _html_section("4. Recommendations", rec_html),
            _html_section(
                "5. Appendix",
                "<h3>Video record</h3>"
                f"{recording_block}"
                "<h3>Screenshots</h3>"
                f"{shots_html}"
                "<h3>Related files</h3>"
                "<ul>"
                f'<li><a href="{html.escape(PERSONA_REPORT_FILENAME)}">persona_report.md</a></li>'
                '<li><a href="ux_result.json">ux_result.json</a></li>'
                '<li><a href="action_trace.json">action_trace.json</a></li>'
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
  <title>User Testing Report — {html.escape(config.persona)}</title>
  <style>
    body {{ font-family: Georgia, "Times New Roman", serif; line-height: 1.55; max-width: 960px; margin: 2rem auto; padding: 0 1rem; color: #1a1a1a; }}
    h1 {{ font-family: system-ui, sans-serif; border-bottom: 2px solid #222; padding-bottom: 0.5rem; }}
    h2 {{ font-family: system-ui, sans-serif; margin-top: 2rem; color: #222; }}
    h3 {{ font-family: system-ui, sans-serif; margin-top: 1.25rem; color: #333; }}
    img, video {{ max-width: 100%; border: 1px solid #ccc; border-radius: 4px; margin: 0.5rem 0; }}
    code {{ font-family: ui-monospace, monospace; background: #f4f4f4; padding: 0.1rem 0.3rem; border-radius: 3px; }}
    section {{ margin-bottom: 1.5rem; }}
    figure {{ margin: 0.75rem 0; }}
    figcaption {{ font-size: 0.85rem; color: #555; }}
  </style>
</head>
<body>
  <h1>User Testing Report</h1>
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
