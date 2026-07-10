"""Unit tests for Feishu skill reply formatting."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from core.skill_return import (  # noqa: E402
    detect_reply_language,
    format_feishu_error,
    format_feishu_reply,
)


def _sample(*, terminal: str, goal: str, finding: str, report: bool = True) -> dict:
    skill = {
        "return_summary": finding,
    }
    if report:
        skill["report_url"] = "http://170.106.175.128:8080/demo/index.html"
        skill["recording_url"] = "http://170.106.175.128:8080/demo/ux_test_recording.webm"
    return {
        "target": "web",
        "persona": "first-time visitor",
        "goal": goal,
        "terminal_state": terminal,
        "main_finding": finding,
        "summary": "Walkthrough note",
        "output_dir": "/tmp/ux_demo",
        "artifacts": {"index_html": "index.html", "recording": "ux_test_recording.webm"},
        "skill": skill,
        "run_id": "demo",
    }


def test_detect_chinese_from_goal() -> None:
    assert detect_reply_language({"goal": "看看首页是否清楚", "persona": "访客"}) == "zh"


def test_detect_english_default() -> None:
    assert (
        detect_reply_language(
            {"goal": "Check the homepage", "persona": "first-time visitor"}
        )
        == "en"
    )


def test_done_english() -> None:
    text = format_feishu_reply(
        _sample(
            terminal="done",
            goal="Check homepage clarity",
            finding="Homepage main info is visible.",
        )
    )
    assert "Status: Completed" in text
    assert "Summary: Homepage main info is visible." in text
    assert "Full report: http://170.106.175.128:8080/demo/index.html" in text
    assert "Reason:" not in text


def test_blocked_chinese() -> None:
    text = format_feishu_reply(
        _sample(
            terminal="blocked",
            goal="看看首页主要信息是否清楚",
            finding="指针未能对准目标控件。",
        )
    )
    assert "状态: 已阻塞" in text
    assert "原因: 指针未能对准目标控件。" in text
    assert "测试摘要:" in text
    assert "完整报告: http://170.106.175.128:8080/demo/index.html" in text


def test_lang_override() -> None:
    payload = _sample(
        terminal="done",
        goal="Check homepage",
        finding="OK",
    )
    text = format_feishu_reply(payload, lang="zh")
    assert "状态: 已完成" in text


def test_error_chinese_message() -> None:
    text = format_feishu_error(message="缺少目标 URL", lang="zh")
    assert "UX 视觉测试未能完成。" in text
    assert "原因: 缺少目标 URL" in text


def main() -> None:
    test_detect_chinese_from_goal()
    test_detect_english_default()
    test_done_english()
    test_blocked_chinese()
    test_lang_override()
    test_error_chinese_message()
    print("skill_return unit tests OK")


if __name__ == "__main__":
    main()
