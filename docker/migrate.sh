#!/usr/bin/env bash
set -euo pipefail

cd /app

alembic -c database/alembic.ini upgrade head
