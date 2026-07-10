"""Format OpenClaw / Feishu user-facing replies from ux_result.json."""

from __future__ import annotations

import re
from typing import Any, Literal

ReplyLang = Literal["en", "zh"]

_CJK_RE = re.compile(r"[\u3040-\u30ff\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]")

_STATUS_EN = {
    "done": "Completed",
    "blocked": "Blocked",
    "max_steps": "Stopped (max steps)",
    "timeout": "Stopped (timeout)",
}
_STATUS_ZH = {
    "done": "已完成",
    "blocked": "已阻塞",
    "max_steps": "已停止（达到步数上限）",
    "timeout": "已停止（超时）",
}

_LABELS = {
    "en": {
        "status": "Status",
        "reason": "Reason",
        "summary": "Summary",
        "full_report": "Full report",
        "full_report_local": "Full report (local only)",
        "publish_note": "Note: public report URL unavailable — publish env was not set.",
        "recording": "Recording",
        "error_title": "UX visual test could not complete.",
        "error_reason": "Reason",
        "error_detail": "Detail",
        "error_hint": "Please retry with a simpler goal or check runner logs on the VM.",
        "unknown_status": "Unknown",
        "empty_summary": "(no summary)",
        "max_steps_reason": "The walkthrough reached the maximum number of steps without done or blocked.",
        "timeout_reason": "The walkthrough stopped because the run timeout was reached.",
    },
    "zh": {
        "status": "状态",
        "reason": "原因",
        "summary": "测试摘要",
        "full_report": "完整报告",
        "full_report_local": "完整报告（仅本地）",
        "publish_note": "说明：未配置发布环境，暂无公开报告链接。",
        "recording": "录像",
        "error_title": "UX 视觉测试未能完成。",
        "error_reason": "原因",
        "error_detail": "详情",
        "error_hint": "请简化目标后重试，或在 VM 上查看 runner 日志。",
        "unknown_status": "未知",
        "empty_summary": "（无摘要）",
        "max_steps_reason": "未在完成或阻塞前达到最大步数上限。",
        "timeout_reason": "因整体超时而停止。",
    },
}


def contains_cjk(text: str) -> bool:
    return bool(_CJK_RE.search(text or ""))


def detect_reply_language(
    ux_result: dict[str, Any] | None = None,
    *,
    text: str | None = None,
    lang: str | None = None,
) -> ReplyLang:
    """Prefer explicit lang; else detect CJK in user-facing request fields."""
    if lang in ("en", "zh"):
        return lang  # type: ignore[return-value]
    if text and contains_cjk(text):
        return "zh"
    if ux_result:
        blob = " ".join(
            str(ux_result.get(key) or "")
            for key in ("goal", "persona", "summary", "main_finding")
        )
        if contains_cjk(blob):
            return "zh"
    return "en"


def _public_url(
    skill: dict[str, Any],
    key: str,
    *,
    fallback_base: str | None,
    rel_path: str | None,
) -> str | None:
    explicit = skill.get(key)
    if explicit:
        return str(explicit)
    if fallback_base and rel_path:
        return f"{fallback_base.rstrip('/')}/{rel_path.lstrip('/')}"
    return None


def _status_label(terminal_state: str, lang: ReplyLang) -> str:
    table = _STATUS_ZH if lang == "zh" else _STATUS_EN
    return table.get(terminal_state, _LABELS[lang]["unknown_status"])


def _test_summary(ux_result: dict[str, Any], labels: dict[str, str]) -> str:
    skill = ux_result.get("skill") or {}
    for value in (
        skill.get("return_summary"),
        ux_result.get("main_finding"),
        ux_result.get("summary"),
    ):
        if value:
            return str(value).strip()
    return labels["empty_summary"]


def _blocked_or_stop_reason(
    ux_result: dict[str, Any],
    terminal_state: str,
    labels: dict[str, str],
) -> str | None:
    if terminal_state == "blocked":
        return (
            str(ux_result.get("main_finding") or "").strip()
            or str(ux_result.get("summary") or "").strip()
            or None
        )
    if terminal_state == "max_steps":
        finding = str(ux_result.get("main_finding") or "").strip()
        return finding or labels["max_steps_reason"]
    if terminal_state == "timeout":
        finding = str(ux_result.get("main_finding") or "").strip()
        return finding or labels["timeout_reason"]
    return None


def format_feishu_reply(
    ux_result: dict[str, Any],
    *,
    lang: str | None = None,
) -> str:
    """Return concise Feishu text: Status (+ Reason) / Summary / Full report."""
    reply_lang = detect_reply_language(ux_result, lang=lang)
    labels = _LABELS[reply_lang]
    skill = ux_result.get("skill") or {}
    artifacts = ux_result.get("artifacts") or {}
    terminal_state = str(ux_result.get("terminal_state") or "unknown")

    lines = [
        f"{labels['status']}: {_status_label(terminal_state, reply_lang)}",
    ]

    reason = _blocked_or_stop_reason(ux_result, terminal_state, labels)
    if reason:
        lines.append(f"{labels['reason']}: {reason}")

    lines.extend(
        [
            "",
            f"{labels['summary']}: {_test_summary(ux_result, labels)}",
            "",
        ]
    )

    report_url = skill.get("report_url")
    if report_url:
        lines.append(f"{labels['full_report']}: {report_url}")
    else:
        index_html = artifacts.get("index_html", "index.html")
        output_dir = ux_result.get("output_dir", "")
        local_report = f"{output_dir}/{index_html}" if output_dir else index_html
        lines.append(f"{labels['full_report_local']}: {local_report}")
        lines.append(labels["publish_note"])

    recording_url = _public_url(
        skill,
        "recording_url",
        fallback_base=skill.get("report_base_url"),
        rel_path=artifacts.get("recording"),
    )
    if recording_url:
        lines.append(f"{labels['recording']}: {recording_url}")

    return "\n".join(lines)


def format_feishu_error(
    *,
    message: str,
    run_id: str | None = None,
    detail: str | None = None,
    lang: str | None = None,
    text: str | None = None,
) -> str:
    reply_lang = detect_reply_language(text=text or message, lang=lang)
    labels = _LABELS[reply_lang]
    lines = [
        labels["error_title"],
        "",
        f"{labels['error_reason']}: {message}",
    ]
    if run_id:
        lines.append(f"Run id: {run_id}")
    if detail:
        lines.append(f"{labels['error_detail']}: {detail}")
    lines.extend(["", labels["error_hint"]])
    return "\n".join(lines)
