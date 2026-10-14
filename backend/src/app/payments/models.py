"""Модель платежа."""

from datetime import UTC, datetime
from enum import StrEnum

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base
from app.payments.status import PaymentStatus


class PaymentMethod(StrEnum):
    """Способы оплаты платежа."""

    CARD = "card"
    SBP = "sbp"
    INSTALLMENT = "installment"


def _utc_now() -> datetime:
    return datetime.now(UTC)


class Payment(Base):
    """Платёж: сумма после скидки, способ оплаты и текущий статус."""

    __tablename__ = "payments"
    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'succeeded', 'failed', 'refunded')",
            name="status_values",
        ),
        CheckConstraint("amount >= 0", name="amount_non_negative"),
        CheckConstraint("discount >= 0", name="discount_non_negative"),
        CheckConstraint("method IN ('card', 'sbp', 'installment')", name="method_values"),
        CheckConstraint(
            "(method = 'installment' AND installment_months IN (3, 6, 12))"
            " OR (method <> 'installment' AND installment_months IS NULL)",
            name="installment_months_consistency",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    status: Mapped[str] = mapped_column(
        String(16), nullable=False, default=PaymentStatus.PENDING, index=True
    )
    tariff_id: Mapped[int] = mapped_column(ForeignKey("tariffs.id"), nullable=False, index=True)
    amount: Mapped[int] = mapped_column(nullable=False)
    discount: Mapped[int] = mapped_column(nullable=False, default=0)
    method: Mapped[str] = mapped_column(String(16), nullable=False)
    installment_months: Mapped[int | None] = mapped_column(nullable=True)
    email: Mapped[str] = mapped_column(String(320), nullable=False, index=True)
    idempotency_key: Mapped[str | None] = mapped_column(String(255), nullable=True, unique=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utc_now
    )
