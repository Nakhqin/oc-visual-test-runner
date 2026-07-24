#!/usr/bin/env bash
# Run ux_testing.py with publish env, then print Feishu-ready reply on stdout.
#
# Usage:
#   ./scripts/openclaw/invoke_runner.sh RUN_ID TARGET URL PERSONA GOAL [MAX_STEPS] [OPTIONS...]
#
# Options (any order after positional args):
#   --use-stub              Pathway smoke only (skip Gemini)
#   --timeout-seconds N     Overall run timeout (default: 180)
#   --lang en|zh            Feishu reply language override
#
# stdout: Feishu reply (format_skill_reply.py) — send this to the user unchanged
# stderr: runner metadata (openclaw_output_dir=..., openclaw_ux_result=...)
#
# Requires: UX_REPORT_PUBLIC_* (or defaults below), GOOGLE_API_KEY for Gemini runs.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$REPO_ROOT"

RUN_ID="${1:?run_id required}"
TARGET="${2:?target required (figma|web)}"
URL="${3:?url required}"
PERSONA="${4:?persona required}"
GOAL="${5:?goal required}"
shift 5

MAX_STEPS=10
USE_STUB=""
TIMEOUT_SECONDS=180
REPLY_LANG=""

if [[ $# -gt 0 && "$1" =~ ^[0-9]+$ ]]; then
  MAX_STEPS="$1"
  shift
fi

while [[ $# -gt 0 ]]; do
  case "$1" in
    --use-stub)
      USE_STUB=1
      shift
      ;;
    --timeout-seconds)
      TIMEOUT_SECONDS="${2:?--timeout-seconds requires a value}"
      if ! [[ "$TIMEOUT_SECONDS" =~ ^[0-9]+$ ]] || [[ "$TIMEOUT_SECONDS" -lt 1 ]]; then
        echo "error: --timeout-seconds must be a positive integer" >&2
        exit 2
      fi
      shift 2
      ;;
    --lang)
      REPLY_LANG="${2:?--lang requires en or zh}"
      if [[ "$REPLY_LANG" != "en" && "$REPLY_LANG" != "zh" ]]; then
        echo "error: --lang must be en or zh" >&2
        exit 2
      fi
      shift 2
      ;;
    *)
      echo "error: unknown argument: $1" >&2
      exit 2
      ;;
  esac
done

OUTPUT_DIR="/tmp/ux_${RUN_ID}"

export UX_REPORT_PUBLIC_DIR="${UX_REPORT_PUBLIC_DIR:-/var/www/ux-reports}"
export UX_REPORT_PUBLIC_BASE_URL="${UX_REPORT_PUBLIC_BASE_URL:-http://170.106.175.128:8080}"

PYTHON="${REPO_ROOT}/.venv/bin/python3"
if [[ ! -x "$PYTHON" ]]; then
  echo "error: project venv python not found or not executable: ${PYTHON}" >&2
  echo "error: refuse to fall back to system python3 (missing playwright risk)" >&2
  exit 2
fi

export PATH="$(dirname "$PYTHON"):${PATH}"
export LANG="${LANG:-C.UTF-8}"
export PYTHONUTF8="${PYTHONUTF8:-1}"
export PYTHONIOENCODING="${PYTHONIOENCODING:-utf-8}"

FORMAT_LANG_ARGS=()
if [[ -n "$REPLY_LANG" ]]; then
  FORMAT_LANG_ARGS=(--lang "$REPLY_LANG")
fi

detect_reply_lang() {
  if [[ -n "$REPLY_LANG" ]]; then
    echo "$REPLY_LANG"
    return
  fi
  DETECT_TEXT="${PERSONA} ${GOAL}" "$PYTHON" -c "
import os
import sys
sys.path.insert(0, 'scripts')
from core.skill_return import detect_reply_language
print(detect_reply_language(text=os.environ.get('DETECT_TEXT', '')))
"
}

print_feishu_reply() {
  if [[ -f "${OUTPUT_DIR}/ux_result.json" ]]; then
    "$PYTHON" ./scripts/format_skill_reply.py \
      --output-dir "$OUTPUT_DIR" \
      "${FORMAT_LANG_ARGS[@]}"
    return 0
  fi

  local exit_code="${1:-1}"
  local error_msg="Runner exited with code ${exit_code}."
  if [[ "$exit_code" -eq 2 ]]; then
    error_msg="Invalid parameters or missing project venv (exit ${exit_code})."
  fi
  local lang
  lang="$(detect_reply_lang)"
  "$PYTHON" ./scripts/format_skill_reply.py \
    --error "$error_msg" \
    --run-id "$RUN_ID" \
    --lang "$lang"
  return 1
}

ARGS=(
  "$PYTHON" ./scripts/ux_testing.py
  --target "$TARGET"
  --url "$URL"
  --persona "$PERSONA"
  --goal "$GOAL"
  --output-dir "$OUTPUT_DIR"
  --run-id "$RUN_ID"
  --max-steps "$MAX_STEPS"
  --timeout-seconds "$TIMEOUT_SECONDS"
)

if [[ -n "$USE_STUB" ]]; then
  ARGS+=(--use-stub)
fi

set +e
"${ARGS[@]}"
RUNNER_EXIT=$?
set -e

echo "openclaw_output_dir=${OUTPUT_DIR}" >&2
echo "openclaw_ux_result=${OUTPUT_DIR}/ux_result.json" >&2

if print_feishu_reply "$RUNNER_EXIT"; then
  exit 0
fi
exit 1
