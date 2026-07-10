#!/usr/bin/env python3
"""Print Feishu-ready reply text from a completed run's ux_result.json."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from core.skill_return import format_feishu_error, format_feishu_reply  # noqa: E402


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="format_skill_reply.py",
        description="Format ux_result.json as a Feishu user-facing reply.",
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--ux-result",
        type=Path,
        help="Path to ux_result.json",
    )
    group.add_argument(
        "--output-dir",
        type=Path,
        help="Run output directory containing ux_result.json",
    )
    parser.add_argument(
        "--error",
        default=None,
        help="Format a failure reply instead of success (pass error message)",
    )
    parser.add_argument(
        "--run-id",
        default=None,
        help="Run id for --error replies",
    )
    parser.add_argument(
        "--lang",
        choices=["en", "zh"],
        default=None,
        help="Reply language (default: detect from goal/persona CJK)",
    )
    return parser


def resolve_ux_result_path(args: argparse.Namespace) -> Path:
    if args.ux_result is not None:
        return args.ux_result
    return args.output_dir / "ux_result.json"


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.error is not None:
        print(
            format_feishu_error(
                message=args.error,
                run_id=args.run_id,
                lang=args.lang,
            )
        )
        return 1

    path = resolve_ux_result_path(args)
    if not path.is_file():
        print(
            format_feishu_error(
                message=f"ux_result.json not found: {path}",
                run_id=args.run_id,
                lang=args.lang,
            )
        )
        return 1

    payload = json.loads(path.read_text(encoding="utf-8"))
    print(format_feishu_reply(payload, lang=args.lang))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
