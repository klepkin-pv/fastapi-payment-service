"""HTTP-эндпоинт вебхука банка."""

from typing import Annotated

from fastapi import APIRouter, Depends, Header, Request
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.db import get_session
from app.webhooks.schemas import PaymentStatusChange
from app.webhooks.service import change_payment_status
from app.webhooks.signature import InvalidSignatureError, verify_signature

router = APIRouter()


@router.post(
    "/webhooks/bank",
    openapi_extra={
        "requestBody": {
            "required": True,
            "content": {"application/json": {"schema": PaymentStatusChange.model_json_schema()}},
        }
    },
)
async def bank_webhook(
    request: Request,
    session: Annotated[Session, Depends(get_session)],
    x_signature: Annotated[str | None, Header()] = None,
) -> dict[str, str]:
    """Проверяет подпись X-Signature, затем меняет статус платежа по телу вебхука."""
    raw_body = await request.body()
    if not verify_signature(raw_body, x_signature, settings.webhook_secret):
        raise InvalidSignatureError()

    try:
        change = PaymentStatusChange.model_validate_json(raw_body)
    except ValidationError as exc:
        raise RequestValidationError(exc.errors()) from exc

    change_payment_status(session, change.payment_id, change.status)
    return {"result": "ok"}
