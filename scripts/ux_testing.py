#!/usr/bin/env python3
"""CLI entrypoint for oc-visual-test-runner."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from core.config import (  # noqa: E402
    DEFAULT_MAX_STEPS,
    DEFAULT_TIMEOUT_SECONDS,
    ConfigError,
    TargetConfig,
    build_target_config,
)


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
    return parser


def parse_args(argv: list[str] | None = None) -> TargetConfig:
    parser = build_parser()
    args = parser.parse_args(argv)
    return build_target_config(
        target=args.target,
        url=args.url,
        persona=args.persona,
        goal=args.goal,
        output_dir=args.output_dir,
        max_steps=args.max_steps,
        timeout_seconds=args.timeout_seconds,
    )


def main(argv: list[str] | None = None) -> int:
    try:
        config = parse_args(argv)
    except ConfigError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    print(
        "Config validated. Visual agent loop and browser adapter are not implemented yet.",
        file=sys.stderr,
    )
    print(
        f"target={config.target} url={config.url} output_dir={config.output_dir}",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
