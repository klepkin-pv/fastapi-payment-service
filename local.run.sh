#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

uv run --project backend alembic -c database/alembic.ini upgrade head
uv run --project backend uvicorn app.main:app --reload --port 8000
