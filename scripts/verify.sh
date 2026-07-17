#!/usr/bin/env bash
# Unified verify for Silent Shield
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo "==> Backend lint (ruff)"
(cd backend && ruff check app tests)

if [[ "${1:-}" != "--quick" ]]; then
  echo "==> Backend tests"
  (cd backend && python -m pytest -q -m "not slow and not eval")
fi

if [[ -f frontend/package.json ]]; then
  echo "==> Frontend lint"
  npm run lint --prefix frontend
  if [[ "${1:-}" != "--quick" ]]; then
    echo "==> Frontend tests"
    npm test --prefix frontend
  fi
else
  echo "WARN: frontend not scaffolded yet; skip"
fi

echo "All verify steps passed."
