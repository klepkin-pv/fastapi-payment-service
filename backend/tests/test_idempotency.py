"""Тесты идемпотентности POST /payments по заголовку Idempotency-Key (ТЗ #3)."""

from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.payments.models import Payment

CARD_PAYMENT = {"tariff_id": 2, "email": "student@example.com", "method": "card"}
SBP_PAYMENT = {"tariff_id": 3, "email": "other@example.com", "method": "sbp"}


def _count_payments(session: Session) -> int:
    """Считает платежи в базе данных."""
    return session.scalar(select(func.count(Payment.id))) or 0


def test_repeated_key_returns_first_payment(client: TestClient, session: Session) -> None:
    """Повтор с тем же Idempotency-Key: 200, тот же id, в базе один платёж (ТЗ #3)."""
    first = client.post("/payments", json=CARD_PAYMENT, headers={"Idempotency-Key": "order-1"})
    second = client.post("/payments", json=SBP_PAYMENT, headers={"Idempotency-Key": "order-1"})

    assert first.status_code == 201
    assert second.status_code == 200
    assert second.json()["id"] == first.json()["id"]
    assert _count_payments(session) == 1


def test_repeated_key_returns_first_payment_body(client: TestClient) -> None:
    """Повтор с другим телом возвращает данные первого платежа (ТЗ #3)."""
    first = client.post("/payments", json=CARD_PAYMENT, headers={"Idempotency-Key": "order-2"})
    second = client.post("/payments", json=SBP_PAYMENT, headers={"Idempotency-Key": "order-2"})

    assert second.status_code == 200
    body = second.json()
    first_body = first.json()
    body.pop("created_at")
    first_body.pop("created_at")

    assert body == first_body


def test_without_key_each_request_creates_payment(client: TestClient, session: Session) -> None:
    """Без Idempotency-Key два одинаковых POST создают два платежа (ТЗ #3)."""
    first = client.post("/payments", json=CARD_PAYMENT)
    second = client.post("/payments", json=CARD_PAYMENT)

    assert first.status_code == 201
    assert second.status_code == 201
    assert second.json()["id"] != first.json()["id"]
    assert _count_payments(session) == 2


def test_different_keys_create_two_payments(client: TestClient, session: Session) -> None:
    """Разные ключи идемпотентности создают два разных платежа (ТЗ #3)."""
    first = client.post("/payments", json=CARD_PAYMENT, headers={"Idempotency-Key": "a"})
    second = client.post("/payments", json=CARD_PAYMENT, headers={"Idempotency-Key": "b"})

    assert second.json()["id"] != first.json()["id"]
    assert _count_payments(session) == 2


def test_too_long_key_is_rejected(client: TestClient, session: Session) -> None:
    """Ключ длиннее 255 символов отклоняется с 422 и не создаёт платёж."""
    response = client.post("/payments", json=CARD_PAYMENT, headers={"Idempotency-Key": "k" * 256})

    assert response.status_code == 422
    assert _count_payments(session) == 0
