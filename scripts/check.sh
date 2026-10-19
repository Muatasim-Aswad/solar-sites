#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
uv run --no-sync --project apps/backend ruff check apps/backend e2e scripts
uv run --no-sync --project apps/backend ruff format --check apps/backend e2e scripts
bash -n scripts/check.sh scripts/verify.sh scripts/container/smoke.sh .githooks/pre-commit
pnpm --dir apps/frontend run lint
pnpm --dir apps/frontend exec vp lint "$PWD/e2e" "$PWD/playwright.config.ts"
pnpm --dir apps/frontend exec vp fmt --check
pnpm --dir apps/frontend exec vp fmt --check "$PWD/e2e" "$PWD/playwright.config.ts" "$PWD/package.json" "$PWD/tsconfig.json"
