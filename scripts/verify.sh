#!/usr/bin/env bash
# Unified verify for Silent Shield
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo "==> Agent rules wiring"
test -f RULES.md
test -f AGENTS.md
grep -q 'AGENTS\.md' RULES.md
grep -q 'RULES\.md' AGENTS.md
for entrypoint in \
  CLAUDE.md \
  .cursor/rules/project.mdc \
  .github/copilot-instructions.md; do
  test -f "$entrypoint"
  grep -q 'AGENTS\.md' "$entrypoint"
done

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
    if grep -q 'No frontend tests yet' frontend/package.json; then
      echo "WARN: Frontend tests are a placeholder; this is not behavioral test evidence"
    fi
    echo "==> Frontend production build"
    npm run build --prefix frontend
  fi
else
  echo "WARN: frontend not scaffolded yet; skip"
fi

echo "All verify steps passed."
