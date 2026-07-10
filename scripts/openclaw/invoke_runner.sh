#!/usr/bin/env bash
# Invoke ux_testing.py with publish env for OpenClaw (same VM).
# Usage:
#   ./scripts/openclaw/invoke_runner.sh RUN_ID TARGET URL PERSONA GOAL [MAX_STEPS]
#
# Requires: UX_REPORT_PUBLIC_* (or set below), GOOGLE_API_KEY for Gemini runs.
# Optional: add --use-stub as 7th arg for pathway smoke only.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$REPO_ROOT"

RUN_ID="${1:?run_id required}"
TARGET="${2:?target required (figma|web)}"
URL="${3:?url required}"
PERSONA="${4:?persona required}"
GOAL="${5:?goal required}"
MAX_STEPS="${6:-10}"
USE_STUB="${7:-}"

OUTPUT_DIR="/tmp/ux_${RUN_ID}"

export UX_REPORT_PUBLIC_DIR="${UX_REPORT_PUBLIC_DIR:-/var/www/ux-reports}"
export UX_REPORT_PUBLIC_BASE_URL="${UX_REPORT_PUBLIC_BASE_URL:-http://170.106.175.128:8080}"

PYTHON="${REPO_ROOT}/.venv/bin/python3"
if [[ ! -x "$PYTHON" ]]; then
  echo "error: project venv python not found or not executable: ${PYTHON}" >&2
  echo "error: refuse to fall back to system python3 (missing playwright risk)" >&2
  exit 2
fi

# Ensure venv bin is first on PATH for child tools
export PATH="$(dirname "$PYTHON"):${PATH}"
export LANG="${LANG:-C.UTF-8}"
export PYTHONUTF8="${PYTHONUTF8:-1}"
export PYTHONIOENCODING="${PYTHONIOENCODING:-utf-8}"

ARGS=(
  "$PYTHON" ./scripts/ux_testing.py
  --target "$TARGET"
  --url "$URL"
  --persona "$PERSONA"
  --goal "$GOAL"
  --output-dir "$OUTPUT_DIR"
  --run-id "$RUN_ID"
  --max-steps "$MAX_STEPS"
)

if [[ "$USE_STUB" == "--use-stub" ]]; then
  ARGS+=(--use-stub)
fi

"${ARGS[@]}"
EXIT=$?

echo "openclaw_output_dir=${OUTPUT_DIR}" >&2
echo "openclaw_ux_result=${OUTPUT_DIR}/ux_result.json" >&2

exit "$EXIT"
