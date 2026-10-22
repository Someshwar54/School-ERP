#!/usr/bin/env bash
# Starts a throwaway backend for browser tests: fresh e2e database, migrated and seeded.
set -euo pipefail
cd "$(dirname "$0")/../backend"
export APP_ENV=test ENV_FILE=env/e2e.env   # all e2e settings live in backend/env/e2e.env
./.venv/bin/alembic downgrade base >/dev/null
./.venv/bin/alembic upgrade head >/dev/null
./.venv/bin/python -m app.seed.demo
exec ./.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port "${E2E_API_PORT:-8100}"
