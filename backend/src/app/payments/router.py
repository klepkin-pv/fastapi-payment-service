"""HTTP-эндпоинты платежей."""

from typing import Annotated

from fastapi import APIRouter, Depends, Header, Response
from sqlalchemy.orm import Session

from app.core.db import get_session
from app.payments.repository import list_payments
from app.payments.schemas import PaymentCreate, PaymentOut
from app.payments.service import create_payment, get_payment
from app.payments.status import PaymentStatus

router = APIRouter()


@router.post("/payments", response_model=PaymentOut, status_code=201)
def post_payment(
    data: PaymentCreate,
    response: Response,
    session: Annotated[Session, Depends(get_session)],
    idempotency_key: Annotated[str | None, Header(max_length=255)] = None,
) -> PaymentOut:
    """Создаёт платёж; повтор ключа идемпотентности отдаёт прежний платёж с кодом 200."""
    payment, created = create_payment(session, data, idempotency_key)
    if not created:
        response.status_code = 200
    return PaymentOut.from_payment(payment)


@router.get("/payments", response_model=list[PaymentOut])
def get_payments(
    session: Annotated[Session, Depends(get_session)],
    email: str | None = None,
    status: PaymentStatus | None = None,
) -> list[PaymentOut]:
    """Возвращает платежи с необязательными фильтрами по email и статусу."""
    payments = list_payments(session, email, status)
    return [PaymentOut.from_payment(payment) for payment in payments]


@router.get("/payments/{payment_id}", response_model=PaymentOut)
def get_payment_by_id(
    payment_id: int, session: Annotated[Session, Depends(get_session)]
) -> PaymentOut:
    """Возвращает платёж по идентификатору."""
    return PaymentOut.from_payment(get_payment(session, payment_id))
