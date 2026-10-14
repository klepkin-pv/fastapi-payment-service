"""Перевод доменных ошибок в HTTP-ответы по ТЗ."""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.payments.promo import UnknownPromoCodeError
from app.payments.service import PaymentNotFoundError
from app.payments.status import InvalidTransitionError
from app.tariffs.repository import UnknownTariffError
from app.webhooks.signature import InvalidSignatureError


def register_error_handlers(app: FastAPI) -> None:
    """Регистрирует обработчики доменных исключений."""

    @app.exception_handler(UnknownPromoCodeError)
    async def _unknown_promo_code(request: Request, exc: UnknownPromoCodeError) -> JSONResponse:
        return JSONResponse(status_code=422, content={"detail": "unknown promo code"})

    @app.exception_handler(UnknownTariffError)
    async def _unknown_tariff(request: Request, exc: UnknownTariffError) -> JSONResponse:
        return JSONResponse(status_code=422, content={"detail": "unknown tariff"})

    @app.exception_handler(PaymentNotFoundError)
    async def _payment_not_found(request: Request, exc: PaymentNotFoundError) -> JSONResponse:
        return JSONResponse(status_code=404, content={"detail": "payment not found"})

    @app.exception_handler(InvalidTransitionError)
    async def _invalid_transition(request: Request, exc: InvalidTransitionError) -> JSONResponse:
        return JSONResponse(status_code=409, content={"error": "invalid_transition"})

    @app.exception_handler(InvalidSignatureError)
    async def _invalid_signature(request: Request, exc: InvalidSignatureError) -> JSONResponse:
        return JSONResponse(status_code=401, content={"detail": "invalid signature"})
