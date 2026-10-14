"""Тесты статусов платежа: таблица переходов и вебхук банка (ТЗ #4)."""

import hashlib
import hmac
import json

import httpx
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.payments.models import Payment
from app.payments.status import PaymentStatus, can_transition

WEBHOOK_SECRET = "test-secret"

ALLOWED_TRANSITIONS = [
    (PaymentStatus.PENDING, PaymentStatus.SUCCEEDED),
    (PaymentStatus.PENDING, PaymentStatus.FAILED),
    (PaymentStatus.SUCCEEDED, PaymentStatus.REFUNDED),
]

FORBIDDEN_TRANSITIONS = [
    (PaymentStatus.PENDING, PaymentStatus.PENDING),
    (PaymentStatus.PENDING, PaymentStatus.REFUNDED),
    (PaymentStatus.SUCCEEDED, PaymentStatus.SUCCEEDED),
    (PaymentStatus.SUCCEEDED, PaymentStatus.FAILED),
    (PaymentStatus.FAILED, PaymentStatus.PENDING),
    (PaymentStatus.FAILED, PaymentStatus.SUCCEEDED),
    (PaymentStatus.FAILED, PaymentStatus.FAILED),
    (PaymentStatus.FAILED, PaymentStatus.REFUNDED),
    (PaymentStatus.REFUNDED, PaymentStatus.PENDING),
    (PaymentStatus.REFUNDED, PaymentStatus.SUCCEEDED),
    (PaymentStatus.REFUNDED, PaymentStatus.FAILED),
    (PaymentStatus.REFUNDED, PaymentStatus.REFUNDED),
]


@pytest.mark.parametrize(("current", "target"), ALLOWED_TRANSITIONS)
def test_allowed_transitions(current: PaymentStatus, target: PaymentStatus) -> None:
    """Разрешены: pending → succeeded/failed и succeeded → refunded."""
    assert can_transition(current, target)


@pytest.mark.parametrize(("current", "target"), FORBIDDEN_TRANSITIONS)
def test_forbidden_transitions(current: PaymentStatus, target: PaymentStatus) -> None:
    """Запрещены: succeeded → succeeded/failed, все переходы из failed и refunded."""
    assert can_transition(current, target) is False


def _create_payment(client: TestClient) -> int:
    """Создаёт платёж в статусе pending и возвращает его идентификатор."""
    response = client.post(
        "/payments",
        json={"tariff_id": 2, "email": "student@example.com", "method": "card"},
    )
    assert response.status_code == 201
    return response.json()["id"]


def _send_webhook(client: TestClient, payment_id: int, status: str) -> httpx.Response:
    """Отправляет подписанный вебхук банка со сменой статуса платежа."""
    body = json.dumps({"payment_id": payment_id, "status": status}).encode()
    signature = hmac.new(WEBHOOK_SECRET.encode(), body, hashlib.sha256).hexdigest()
    return client.post(
        "/webhooks/bank",
        content=body,
        headers={"Content-Type": "application/json", "X-Signature": signature},
    )


def _db_status(session: Session, payment_id: int) -> str:
    """Читает статус платежа из базы данных."""
    return session.scalar(select(Payment.status).where(Payment.id == payment_id))


def test_pending_to_succeeded_to_refunded(client: TestClient, session: Session) -> None:
    """Разрешены переходы pending → succeeded и succeeded → refunded (ТЗ #4)."""
    payment_id = _create_payment(client)

    succeeded = _send_webhook(client, payment_id, "succeeded")

    assert succeeded.status_code == 200
    assert succeeded.json() == {"result": "ok"}
    assert _db_status(session, payment_id) == "succeeded"

    refunded = _send_webhook(client, payment_id, "refunded")

    assert refunded.status_code == 200
    assert refunded.json() == {"result": "ok"}
    assert _db_status(session, payment_id) == "refunded"


def test_pending_to_failed_is_allowed(client: TestClient, session: Session) -> None:
    """Разрешён переход pending → failed, он сохраняется в базе (ТЗ #4)."""
    payment_id = _create_payment(client)

    response = _send_webhook(client, payment_id, "failed")

    assert response.status_code == 200
    assert _db_status(session, payment_id) == "failed"


def test_repeated_succeeded_is_rejected(client: TestClient, session: Session) -> None:
    """Повтор succeeded → succeeded: 409 с телом ТЗ, статус в базе не меняется (ТЗ #4)."""
    payment_id = _create_payment(client)
    assert _send_webhook(client, payment_id, "succeeded").status_code == 200

    response = _send_webhook(client, payment_id, "succeeded")

    assert response.status_code == 409
    assert response.json() == {"error": "invalid_transition"}
    assert _db_status(session, payment_id) == "succeeded"


def test_failed_cannot_be_refunded(client: TestClient, session: Session) -> None:
    """Запрещён переход failed → refunded: 409 и статус в базе остаётся failed (ТЗ #4)."""
    payment_id = _create_payment(client)
    assert _send_webhook(client, payment_id, "failed").status_code == 200

    response = _send_webhook(client, payment_id, "refunded")

    assert response.status_code == 409
    assert response.json() == {"error": "invalid_transition"}
    assert _db_status(session, payment_id) == "failed"


def test_refunded_cannot_succeed_again(client: TestClient, session: Session) -> None:
    """Запрещён переход refunded → succeeded: 409 и статус в базе остаётся refunded (ТЗ #4)."""
    payment_id = _create_payment(client)
    assert _send_webhook(client, payment_id, "succeeded").status_code == 200
    assert _send_webhook(client, payment_id, "refunded").status_code == 200

    response = _send_webhook(client, payment_id, "succeeded")

    assert response.status_code == 409
    assert response.json() == {"error": "invalid_transition"}
    assert _db_status(session, payment_id) == "refunded"


def test_webhook_unknown_payment_is_404(client: TestClient) -> None:
    """Вебхук с несуществующим payment_id → 404 (ТЗ #4)."""
    response = _send_webhook(client, 999, "succeeded")

    assert response.status_code == 404
    assert response.json() == {"detail": "payment not found"}


@pytest.mark.parametrize("status", ["pending", "cancelled"])
def test_webhook_status_outside_allowed_set_is_422(client: TestClient, status: str) -> None:
    """Статус вне {succeeded, failed, refunded} → 422 (ТЗ #4)."""
    payment_id = _create_payment(client)

    response = _send_webhook(client, payment_id, status)

    assert response.status_code == 422
