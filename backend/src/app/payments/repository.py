"""Запросы к таблице платежей."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.payments.models import Payment


def get_by_id(session: Session, payment_id: int) -> Payment | None:
    """Возвращает платёж по идентификатору или None."""
    return session.get(Payment, payment_id)


def get_by_idempotency_key(session: Session, idempotency_key: str) -> Payment | None:
    """Возвращает платёж, созданный с указанным ключом идемпотентности, или None."""
    return session.scalar(select(Payment).where(Payment.idempotency_key == idempotency_key))


def list_payments(
    session: Session, email: str | None = None, status: str | None = None
) -> list[Payment]:
    """Возвращает платежи по фильтрам, отсортированные по убыванию id."""
    query = select(Payment).order_by(Payment.id.desc())
    if email is not None:
        query = query.where(Payment.email == email)
    if status is not None:
        query = query.where(Payment.status == status)
    return list(session.scalars(query))
