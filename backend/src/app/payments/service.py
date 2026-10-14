"""Сценарии работы с платежами: создание, чтение и смена статуса."""

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.payments import repository
from app.payments.models import Payment
from app.payments.promo import apply_promo
from app.payments.schemas import PaymentCreate
from app.payments.status import InvalidTransitionError, PaymentStatus, can_transition
from app.tariffs.repository import UnknownTariffError, get_tariff


class PaymentNotFoundError(Exception):
    """Платёж с указанным идентификатором не найден."""


def create_payment(
    session: Session, data: PaymentCreate, idempotency_key: str | None
) -> tuple[Payment, bool]:
    """Создаёт платёж; при повторе ключа идемпотентности отдаёт уже созданный."""
    if idempotency_key is not None:
        existing = repository.get_by_idempotency_key(session, idempotency_key)
        if existing is not None:
            return existing, False

    tariff = get_tariff(session, data.tariff_id)
    if tariff is None:
        raise UnknownTariffError(data.tariff_id)

    amount, discount = apply_promo(tariff.price, data.promo_code)
    payment = Payment(
        tariff_id=tariff.id,
        amount=amount,
        discount=discount,
        method=data.method,
        installment_months=data.installment_months,
        email=data.email,
        idempotency_key=idempotency_key,
    )
    session.add(payment)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        if idempotency_key is None:
            raise
        existing = repository.get_by_idempotency_key(session, idempotency_key)
        if existing is None:
            raise
        return existing, False
    return payment, True


def get_payment(session: Session, payment_id: int) -> Payment:
    """Возвращает платёж или поднимает PaymentNotFoundError."""
    payment = repository.get_by_id(session, payment_id)
    if payment is None:
        raise PaymentNotFoundError(payment_id)
    return payment


def apply_status(session: Session, payment_id: int, new_status: PaymentStatus) -> None:
    """Переводит платёж в новый статус, если такой переход разрешён."""
    payment = get_payment(session, payment_id)
    current = PaymentStatus(payment.status)
    if not can_transition(current, new_status):
        raise InvalidTransitionError(current, new_status)
    payment.status = new_status
    session.commit()
