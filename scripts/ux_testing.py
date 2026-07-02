#!/usr/bin/env python3
"""CLI entrypoint for oc-visual-test-runner."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from adapters.browser import BrowserAdapterError  # noqa: E402
from core.config import (  # noqa: E402
    DEFAULT_MAX_STEPS,
    DEFAULT_TIMEOUT_SECONDS,
    ConfigError,
    TargetConfig,
    build_target_config,
)
from core.decision import create_decision_maker  # noqa: E402
from core.loop import run_visual_agent_loop  # noqa: E402
from core.report import selected_persona_report_mode  # noqa: E402
from core.vlm import DEFAULT_GEMINI_MODEL, ENV_GEMINI_MODEL, ENV_GOOGLE_API_KEY  # noqa: E402

ENV_PERSONA_REPORT_GEMINI = "PERSONA_REPORT_GEMINI"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ux_testing.py",
        description=(
            "Run persona-based visual UX walkthroughs for figma and web targets."
        ),
    )
    parser.add_argument(
        "--target",
        required=True,
        choices=["figma", "web"],
        help="Target type: figma prototype URL or web URL",
    )
    parser.add_argument("--url", required=True, help="Figma prototype URL or web URL")
    parser.add_argument(
        "--persona",
        required=True,
        help="Participant persona for VLM reasoning",
    )
    parser.add_argument(
        "--goal",
        required=True,
        help="Task or scenario the persona should attempt",
    )
    parser.add_argument(
        "--output-dir",
        required=True,
        help="Directory for run artifacts",
    )
    parser.add_argument(
        "--max-steps",
        type=int,
        default=DEFAULT_MAX_STEPS,
        help=f"Maximum agent loop iterations (default: {DEFAULT_MAX_STEPS})",
    )
    parser.add_argument(
        "--timeout-seconds",
        type=int,
        default=DEFAULT_TIMEOUT_SECONDS,
        help=f"Overall run timeout in seconds (default: {DEFAULT_TIMEOUT_SECONDS})",
    )
    parser.add_argument(
        "--use-stub",
        action="store_true",
        help="Force stub decision maker (skip Gemini even if GOOGLE_API_KEY is set)",
    )
    parser.add_argument(
        "--persona-report-gemini",
        action="store_true",
        help="Polish persona_report.md with a final Gemini synthesis pass (requires API key)",
    )
    return parser


def _env_flag(name: str) -> bool:
    return os.environ.get(name, "").strip().lower() in {"1", "true", "yes"}


def parse_args(argv: list[str] | None = None) -> tuple[TargetConfig, bool, bool]:
    parser = build_parser()
    args = parser.parse_args(argv)
    config = build_target_config(
        target=args.target,
        url=args.url,
        persona=args.persona,
        goal=args.goal,
        output_dir=args.output_dir,
        max_steps=args.max_steps,
        timeout_seconds=args.timeout_seconds,
    )
    persona_report_gemini = args.persona_report_gemini or _env_flag(ENV_PERSONA_REPORT_GEMINI)
    return config, args.use_stub, persona_report_gemini


def print_selection_metadata(config: TargetConfig, *, persona_report_mode: str) -> None:
    print(f"SELECTED_TARGET={config.target}")
    print("SELECTED_ADAPTER=browser")
    print("SELECTED_RUNNER=visual_agent")
    print("SELECTED_HOVER_LOOP=enabled")
    print("SELECTED_POST_CLICK_VERIFY=enabled")
    print(f"SELECTED_PERSONA_REPORT={persona_report_mode}")


def main(argv: list[str] | None = None) -> int:
    try:
        config, use_stub, persona_report_gemini = parse_args(argv)
    except ConfigError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    decision_maker = create_decision_maker(use_stub=use_stub)
    persona_report_mode = selected_persona_report_mode(
        use_gemini_synthesis=persona_report_gemini,
        decision_source=decision_maker.source,
    )
    print_selection_metadata(config, persona_report_mode=persona_report_mode)
    print(f"SELECTED_DECISION_MAKER={decision_maker.source}", file=sys.stderr)

    gemini_api_key = None if use_stub else os.environ.get(ENV_GOOGLE_API_KEY, "").strip() or None
    gemini_model = os.environ.get(ENV_GEMINI_MODEL, DEFAULT_GEMINI_MODEL).strip()

    try:
        result = run_visual_agent_loop(
            config,
            decision_maker=decision_maker,
            persona_report_gemini=persona_report_gemini,
            gemini_api_key=gemini_api_key,
            gemini_model=gemini_model or DEFAULT_GEMINI_MODEL,
        )
    except BrowserAdapterError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    print(f"terminal_state={result.terminal_state}", file=sys.stderr)
    print(f"steps_taken={result.steps_taken}", file=sys.stderr)
    print(f"action_trace={result.artifacts.action_trace_path}", file=sys.stderr)
    print(f"ux_result={result.artifacts.ux_result_path}", file=sys.stderr)
    if result.artifacts.persona_report_path is not None:
        print(f"persona_report={result.artifacts.persona_report_path}", file=sys.stderr)
    if result.artifacts.report_synthesis is not None:
        print(f"persona_report_synthesis={result.artifacts.report_synthesis}", file=sys.stderr)
    if result.artifacts.recording_path is not None:
        print(f"recording={result.artifacts.recording_path}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
