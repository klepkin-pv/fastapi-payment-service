"""Сборка FastAPI-приложения: жизненный цикл, healthcheck, роутеры."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.config import settings
from app.core.db import SessionLocal
from app.core.errors import register_error_handlers
from app.payments.router import router as payments_router
from app.tariffs.router import router as tariffs_router
from app.tariffs.seeder import seed_tariffs
from app.webhooks.router import router as webhooks_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Проверяет конфигурацию и наполняет базу тарифами при старте приложения."""
    if not settings.webhook_secret:
        raise RuntimeError("WEBHOOK_SECRET не задан: проверка подписи вебхука обязательна")
    with SessionLocal() as session:
        seed_tariffs(session)
    yield


def create_app() -> FastAPI:
    """Собирает приложение, обработчики ошибок и роутеры."""
    app = FastAPI(
        title="API платежей",
        description="Приём оплаты курса: тарифы, платежи, статусы и вебхук банка.",
        lifespan=lifespan,
    )
    register_error_handlers(app)
    app.include_router(tariffs_router)
    app.include_router(payments_router)
    app.include_router(webhooks_router)
    return app


app = create_app()


@app.get("/health")
async def health() -> dict[str, str]:
    """Возвращает признак работоспособности сервиса."""
    return {"status": "ok"}
