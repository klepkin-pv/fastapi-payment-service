"""Статусы платежа и допустимые переходы между ними."""

from enum import StrEnum


class PaymentStatus(StrEnum):
    """Статусы жизненного цикла платежа."""

    PENDING = "pending"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    REFUNDED = "refunded"


class InvalidTransitionError(Exception):
    """Переход платежа между указанными статусами запрещён."""


TRANSITIONS: dict[PaymentStatus, frozenset[PaymentStatus]] = {
    PaymentStatus.PENDING: frozenset({PaymentStatus.SUCCEEDED, PaymentStatus.FAILED}),
    PaymentStatus.SUCCEEDED: frozenset({PaymentStatus.REFUNDED}),
    PaymentStatus.FAILED: frozenset(),
    PaymentStatus.REFUNDED: frozenset(),
}


def can_transition(current: PaymentStatus, target: PaymentStatus) -> bool:
    """Проверяет, разрешён ли переход из текущего статуса платежа в целевой."""
    return target in TRANSITIONS.get(current, frozenset())
