"""Схемы тела вебхука банка."""

from typing import Literal

from pydantic import BaseModel


class PaymentStatusChange(BaseModel):
    """Тело вебхука банка: идентификатор платежа и новый статус."""

    payment_id: int
    status: Literal["succeeded", "failed", "refunded"]
