$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

uv run --project backend alembic -c database/alembic.ini upgrade head
uv run --project backend uvicorn app.main:app --reload --port 8000
