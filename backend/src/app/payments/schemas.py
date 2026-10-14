"""Схемы платежа: тело создания и объект ответа."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, model_validator

from app.payments.models import Payment, PaymentMethod
from app.payments.schedule import INSTALLMENT_MONTHS, build_schedule


class PaymentCreate(BaseModel):
    """Тело создания платежа: тариф, email, способ оплаты, рассрочка и промокод."""

    tariff_id: int
    email: EmailStr
    method: PaymentMethod
    installment_months: int | None = None
    promo_code: str | None = None

    @model_validator(mode="after")
    def validate_installment_months(self) -> "PaymentCreate":
        """Требует месяцы из {3, 6, 12} для рассрочки, у остальных способов их очищает."""
        if self.method == PaymentMethod.INSTALLMENT:
            if self.installment_months not in INSTALLMENT_MONTHS:
                raise ValueError("installment_months must be one of 3, 6, 12")
        else:
            self.installment_months = None
        return self


class PaymentOut(BaseModel):
    """Объект платежа в ответе API: ровно поля ТЗ, график рассрочки вычисляется."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    status: str
    tariff_id: int
    amount: int
    discount: int
    method: str
    installment_months: int | None
    schedule: list[int] | None = None
    email: str
    created_at: datetime

    @classmethod
    def from_payment(cls, payment: Payment) -> "PaymentOut":
        """Собирает ответ по платежу и достраивает график рассрочки."""
        result = cls.model_validate(payment)
        if result.method == PaymentMethod.INSTALLMENT and result.installment_months is not None:
            result.schedule = build_schedule(result.amount, result.installment_months)
        return result
