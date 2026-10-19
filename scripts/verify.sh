#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
bash scripts/check.sh
uv run --no-sync --project apps/backend mypy --config-file apps/backend/pyproject.toml --cache-dir apps/backend/.mypy_cache apps/backend/src
uv run --no-sync --project apps/backend pyright --project apps/backend/pyproject.toml
pnpm --dir apps/frontend exec tsc --noEmit
pnpm exec tsc --noEmit
uv run --no-sync --project apps/backend python scripts/check-openapi.py
pnpm --dir apps/frontend run api:check
mise run test
