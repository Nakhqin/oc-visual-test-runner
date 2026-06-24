#!/usr/bin/env bash
set -euo pipefail

PROJECT_NAME="${1:-}"

if [ -z "$PROJECT_NAME" ]; then
  echo "Usage: ./scripts/init-new-project.sh <project-name>"
  exit 1
fi

# Replace placeholder project name in key files if present.
find . -type f \
  ! -path './.git/*' \
  ! -path './node_modules/*' \
  -exec sed -i.bak "s/TODO_PROJECT_NAME/${PROJECT_NAME}/g" {} +
find . -name '*.bak' -delete

echo "Initialized project: ${PROJECT_NAME}"
echo "Next: update README.md, .cursor/rules/90-project-context.mdc, docs/PRD.md, docs/ARCHITECTURE.md, docs/VERIFY.md"
