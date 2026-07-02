"""Phase 3 persona report: trace synthesis (A) and optional Gemini polish (B)."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from core.config import TargetConfig
from core.vlm import (
    DEFAULT_GEMINI_MODEL,
    VlmDecisionError,
    synthesize_persona_report_with_gemini,
)

PERSONA_REPORT_FILENAME = "persona_report.md"
SYNTHESIS_TRACE_ONLY = "trace_only"
SYNTHESIS_TRACE_GEMINI = "trace+gemini"
SYNTHESIS_GEMINI_FAILED_FALLBACK = "gemini_failed_fallback"

_PERSONA_NOTE_STUB = (
    "> Decision source: stub — narrative uses placeholder decision text for smoke testing."
)


@dataclass(frozen=True)
class PersonaReportResult:
    content: str
    synthesis: str
    optional_findings: list[dict[str, Any]]


def _to_first_person(reason: str | None) -> str:
    if not reason or not reason.strip():
        return "I continued without noting a specific reason."
    text = reason.strip()
    if re.match(r"^I\b", text):
        return text
    if text.lower().startswith("the "):
        return f"I noticed {text[4:]}"
    if text.lower().startswith("this "):
        return f"I saw that {text[5:]}"
    return f"I felt that {text}"


def _verification_persona_note(verification: dict[str, Any] | None) -> str | None:
    if not verification or not verification.get("applied"):
        return None
    outcome = verification.get("outcome")
    if outcome == "visible_change":
        return "After I clicked, the page seemed to change."
    if outcome == "no_visible_change":
        return "After I clicked, I could not see an obvious change on the page."
    if outcome == "execution_failed":
        return "My click did not seem to go through properly."
    return None


def _describe_intent(action: dict[str, Any]) -> str:
    action_type = action.get("type", "unknown")
    if action_type == "click":
        return f"I intended to click around ({action.get('x')}, {action.get('y')})."
    if action_type == "click_current":
        return "I confirmed the click at the pointer position."
    if action_type == "move_to":
        return f"I moved the pointer to ({action.get('x')}, {action.get('y')})."
    if action_type == "scroll":
        return "I scrolled to see more of the page."
    if action_type == "wait":
        return "I waited for the page to settle."
    if action_type == "type":
        return f"I typed: {action.get('text', '')!r}."
    if action_type in {"done", "blocked"}:
        return f"I stopped because the run reached `{action_type}`."
    return f"I chose action `{action_type}`."


def _terminal_reason_from_trace(steps: list[dict[str, Any]]) -> tuple[str | None, dict[str, Any] | None]:
    if not steps:
        return None, None
    last = steps[-1]
    hover = last.get("hover")
    if isinstance(hover, dict):
        hover_action = hover.get("decision", {}).get("action", {})
        if hover_action.get("type") in {"done", "blocked"}:
            return hover_action.get("reason"), hover_action
    observe_action = last.get("decision", {}).get("action", {})
    if observe_action.get("type") in {"done", "blocked"}:
        return observe_action.get("reason"), observe_action
    return None, None


def _setup_section(*, persona: str, goal: str, target: str, url: str) -> str:
    return "\n".join(
        [
            "## 我是谁，想完成什么",
            "",
            f"我是 **{persona}**。这次我要做的是：**{goal}**。",
            f"我访问的是 **{target}**：<{url}>。",
        ]
    )


def _outcome_section(
    *,
    terminal_state: str,
    terminal_reason: str | None,
    main_finding: str,
) -> str:
    lines = [
        "## 最后怎么样了",
        "",
    ]
    if terminal_state == "done":
        if terminal_reason:
            lines.append(_to_first_person(terminal_reason))
        else:
            lines.append("我认为目标已经完成了。")
    elif terminal_state == "blocked":
        if terminal_reason:
            lines.append(_to_first_person(terminal_reason))
        elif main_finding:
            lines.append(_to_first_person(main_finding))
        else:
            lines.append("我没能继续完成目标。")
    elif terminal_state == "max_steps":
        lines.append("我还没完成目标，这次 walkthrough 就达到了步数上限。")
    elif terminal_state == "timeout":
        lines.append("我还没完成目标，时间就用完了。")
    else:
        lines.append(f"这次 walkthrough 以 `{terminal_state}` 结束。")
    return "\n".join(lines)


def _journey_section_clean(steps: list[dict[str, Any]]) -> str:
    lines = ["## 我一路是怎么操作的", ""]
    if not steps:
        lines.append("_No steps were recorded._")
        return "\n".join(lines)

    for step in steps:
        step_index = step.get("step")
        action = step.get("decision", {}).get("action", {})
        reason = action.get("reason")
        lines.append(f"### Step {step_index}")
        lines.append("")
        lines.append(_describe_intent(action))
        lines.append(_to_first_person(reason))

        hover = step.get("hover")
        if isinstance(hover, dict):
            hover_action = hover.get("decision", {}).get("action", {})
            hover_reason = hover_action.get("reason")
            lines.append("")
            lines.append("After moving the pointer there:")
            lines.append(_to_first_person(hover_reason))
            hover_execution = hover.get("execution")
            if isinstance(hover_execution, dict):
                note = _verification_persona_note(hover_execution.get("verification"))
                if note:
                    lines.append(note)

        execution = step.get("execution")
        if isinstance(execution, dict) and not isinstance(hover, dict):
            note = _verification_persona_note(execution.get("verification"))
            if note:
                lines.append(note)
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def _friction_section(
    steps: list[dict[str, Any]],
    *,
    terminal_state: str,
    terminal_reason: str | None,
) -> str:
    lines = ["## 哪里让我犹豫或卡住了", ""]
    points: list[str] = []

    if terminal_state in {"blocked", "done"} and terminal_reason:
        points.append(_to_first_person(terminal_reason))

    for step in steps:
        for key in ("execution",):
            execution = step.get(key)
            if not isinstance(execution, dict):
                continue
            verification = execution.get("verification")
            if not isinstance(verification, dict):
                continue
            if verification.get("outcome") == "no_visible_change":
                step_index = step.get("step")
                points.append(
                    f"At step {step_index}, I clicked but could not see an obvious response from the page."
                )
        hover = step.get("hover")
        if isinstance(hover, dict):
            execution = hover.get("execution")
            if isinstance(execution, dict):
                verification = execution.get("verification")
                if isinstance(verification, dict) and verification.get("outcome") == "no_visible_change":
                    step_index = step.get("step")
                    points.append(
                        f"At step {step_index}, after confirming a click, the page still looked unchanged to me."
                    )

    if not points:
        lines.append("Nothing stood out as a major sticking point in this run.")
    else:
        for point in points:
            lines.append(f"- {point}")
    lines.append("")
    lines.append(
        "_These are my participant observations only. They are not automatic UX defect classifications._"
    )
    return "\n".join(lines)


def _collect_evidence_paths(
    output_dir: Path,
    ux_result: dict[str, Any],
    steps: list[dict[str, Any]],
) -> list[str]:
    paths: list[str] = []
    artifacts = ux_result.get("artifacts", {})
    for key in ("persona_report", "action_trace", "ux_result", "recording"):
        value = artifacts.get(key)
        if value:
            paths.append(str(value))

    seen: set[str] = set()
    for step in steps:
        observation = step.get("observation", {})
        screenshot = observation.get("screenshot")
        if screenshot and screenshot not in seen:
            paths.append(screenshot)
            seen.add(screenshot)
        hover = step.get("hover")
        if isinstance(hover, dict):
            hover_shot = hover.get("observation", {}).get("screenshot")
            if hover_shot and hover_shot not in seen:
                paths.append(hover_shot)
                seen.add(hover_shot)
            execution = hover.get("execution")
            if isinstance(execution, dict):
                verification = execution.get("verification")
                if isinstance(verification, dict):
                    for attempt in verification.get("attempts", []):
                        for shot_key in ("before_screenshot", "after_screenshot"):
                            shot = attempt.get(shot_key)
                            if shot and shot not in seen:
                                paths.append(shot)
                                seen.add(shot)

    return paths


def _verification_stats(steps: list[dict[str, Any]]) -> dict[str, int]:
    stats = {
        "visible_change": 0,
        "no_visible_change": 0,
        "execution_failed": 0,
        "not_applicable": 0,
    }
    for step in steps:
        for container in (step, step.get("hover") if isinstance(step.get("hover"), dict) else None):
            if not isinstance(container, dict):
                continue
            execution = container.get("execution")
            if not isinstance(execution, dict):
                continue
            verification = execution.get("verification")
            if not isinstance(verification, dict) or not verification.get("applied"):
                continue
            outcome = verification.get("outcome", "not_applicable")
            if outcome in stats:
                stats[outcome] += 1
    return stats


def derive_optional_findings(
    *,
    terminal_state: str,
    main_finding: str,
    classifications: list[str],
) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    for classification in classifications:
        findings.append(
            {
                "tag": classification.replace(" ", "-"),
                "criteria": "ux_result.classifications contains entry",
                "evidence": "see reviewer notes and terminal outcome",
                "note": "runner-inferred; not automatic UX defect",
            }
        )

    blocked_reason = main_finding.lower()
    if terminal_state == "blocked" and "prototype" in blocked_reason:
        findings.append(
            {
                "tag": "prototype-limitation",
                "criteria": "terminal_state=blocked and main_finding mentions prototype",
                "evidence": main_finding,
                "note": "runner-inferred; not automatic UX defect",
            }
        )
    return findings


def _reviewer_notes_section(
    *,
    classifications: list[str],
    verification_stats: dict[str, int],
    optional_findings: list[dict[str, Any]],
    decision_source: str,
) -> str:
    lines = ["## 审查者备注", ""]
    lines.append(f"- Decision source: `{decision_source}`")
    lines.append(f"- Classifications: {classifications or '(none)'}")
    lines.append(
        "- Verification stats (telemetry): "
        + ", ".join(f"{key}={value}" for key, value in verification_stats.items())
    )
    lines.append("")
    lines.append("### Optional findings")
    lines.append("")
    if optional_findings:
        for finding in optional_findings:
            lines.append(
                f"- **{finding['tag']}** — criteria: {finding['criteria']}; "
                f"evidence: {finding['evidence']}; note: {finding['note']}"
            )
    else:
        lines.append("No optional findings tagged under Phase 3 criteria.")
    return "\n".join(lines)


def _evidence_section(paths: list[str]) -> str:
    lines = ["## 给审查者的证据", ""]
    if not paths:
        lines.append("_No evidence paths recorded._")
        return "\n".join(lines)
    for path in paths:
        lines.append(f"- `{path}`")
    return "\n".join(lines)


def build_trace_persona_report(
    config: TargetConfig,
    *,
    trace_payload: dict[str, Any],
    ux_result: dict[str, Any],
    decision_source: str,
) -> str:
    steps = trace_payload.get("steps", [])
    terminal_state = ux_result.get("terminal_state", "unknown")
    main_finding = ux_result.get("main_finding", "")
    classifications = ux_result.get("classifications", [])
    terminal_reason, _ = _terminal_reason_from_trace(steps)
    optional_findings = derive_optional_findings(
        terminal_state=terminal_state,
        main_finding=main_finding,
        classifications=classifications,
    )
    verification_stats = _verification_stats(steps)
    evidence_paths = _collect_evidence_paths(config.output_dir, ux_result, steps)
    if PERSONA_REPORT_FILENAME not in evidence_paths:
        evidence_paths.insert(0, PERSONA_REPORT_FILENAME)

    sections = [
        f"# 我的体验记录 — {config.persona}",
        "",
    ]
    if decision_source == "stub":
        sections.extend([_PERSONA_NOTE_STUB, ""])

    sections.extend(
        [
            _setup_section(
                persona=config.persona,
                goal=config.goal,
                target=config.target,
                url=config.url,
            ),
            "",
            _outcome_section(
                terminal_state=terminal_state,
                terminal_reason=terminal_reason,
                main_finding=main_finding,
            ),
            "",
            _journey_section_clean(steps),
            "",
            _friction_section(
                steps,
                terminal_state=terminal_state,
                terminal_reason=terminal_reason,
            ),
            "",
            _evidence_section(evidence_paths),
            "",
            _reviewer_notes_section(
                classifications=classifications,
                verification_stats=verification_stats,
                optional_findings=optional_findings,
                decision_source=decision_source,
            ),
        ]
    )
    return "\n".join(sections).rstrip() + "\n"


def generate_persona_report(
    config: TargetConfig,
    *,
    trace_payload: dict[str, Any],
    ux_result: dict[str, Any],
    decision_source: str,
    use_gemini_synthesis: bool = False,
    api_key: str | None = None,
    model_name: str = DEFAULT_GEMINI_MODEL,
) -> PersonaReportResult:
    draft = build_trace_persona_report(
        config,
        trace_payload=trace_payload,
        ux_result=ux_result,
        decision_source=decision_source,
    )
    optional_findings = derive_optional_findings(
        terminal_state=ux_result.get("terminal_state", "unknown"),
        main_finding=ux_result.get("main_finding", ""),
        classifications=ux_result.get("classifications", []),
    )

    if not use_gemini_synthesis or not api_key:
        return PersonaReportResult(
            content=draft,
            synthesis=SYNTHESIS_TRACE_ONLY,
            optional_findings=optional_findings,
        )

    try:
        polished = synthesize_persona_report_with_gemini(
            draft=draft,
            config=config,
            terminal_state=ux_result.get("terminal_state", "unknown"),
            api_key=api_key,
            model_name=model_name,
        )
        return PersonaReportResult(
            content=polished,
            synthesis=SYNTHESIS_TRACE_GEMINI,
            optional_findings=optional_findings,
        )
    except VlmDecisionError:
        return PersonaReportResult(
            content=draft,
            synthesis=SYNTHESIS_GEMINI_FAILED_FALLBACK,
            optional_findings=optional_findings,
        )


def write_persona_report(
    config: TargetConfig,
    *,
    trace_payload: dict[str, Any],
    ux_result: dict[str, Any],
    decision_source: str,
    use_gemini_synthesis: bool = False,
    api_key: str | None = None,
    model_name: str = DEFAULT_GEMINI_MODEL,
) -> tuple[Path, PersonaReportResult]:
    report = generate_persona_report(
        config,
        trace_payload=trace_payload,
        ux_result=ux_result,
        decision_source=decision_source,
        use_gemini_synthesis=use_gemini_synthesis,
        api_key=api_key,
        model_name=model_name,
    )
    report_path = config.output_dir / PERSONA_REPORT_FILENAME
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(report.content, encoding="utf-8")

    ux_result_path = config.output_dir / "ux_result.json"
    updated = dict(ux_result)
    artifacts = dict(updated.get("artifacts", {}))
    artifacts["persona_report"] = PERSONA_REPORT_FILENAME
    updated["artifacts"] = artifacts
    updated["report"] = {
        "synthesis": report.synthesis,
        "persona_voice": True,
        "optional_findings": report.optional_findings,
    }
    ux_result_path.write_text(json.dumps(updated, indent=2) + "\n", encoding="utf-8")
    return report_path, report


def selected_persona_report_mode(*, use_gemini_synthesis: bool, decision_source: str) -> str:
    if use_gemini_synthesis and decision_source != "stub":
        return "trace+gemini"
    return "trace"
