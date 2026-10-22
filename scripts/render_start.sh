#!/usr/bin/env bash
# Start command for the hosted demo backend (Render): migrate, seed fictional data, serve.
set -euo pipefail
cd "$(dirname "$0")/../backend"
alembic upgrade head
python -m app.seed.demo
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}" --proxy-headers --forwarded-allow-ips='*'
