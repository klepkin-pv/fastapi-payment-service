"""Смена статуса платежа по вебхуку банка."""

from sqlalchemy.orm import Session

from app.payments.service import apply_status
from app.payments.status import PaymentStatus


def change_payment_status(session: Session, payment_id: int, status: str) -> None:
    """Применяет статус из вебхука через сервис платежей."""
    apply_status(session, payment_id, PaymentStatus(status))
