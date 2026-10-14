"""Тесты бонусного GET /payments с фильтрами по email и статусу."""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.payments.models import Payment


def _create_payment(client: TestClient, email: str) -> int:
    """Создаёт платёж с указанным email и возвращает его идентификатор."""
    response = client.post(
        "/payments",
        json={"tariff_id": 1, "email": email, "method": "card"},
    )
    assert response.status_code == 201
    return response.json()["id"]


def _set_status(session: Session, payment_id: int, status: str) -> None:
    """Задаёт платежу статус напрямую в базе для подготовки данных теста."""
    payment = session.get(Payment, payment_id)
    assert payment is not None
    payment.status = status
    session.commit()


def test_list_returns_newest_first(client: TestClient) -> None:
    """GET /payments отдаёт платежи по убыванию id (бонус ТЗ)."""
    first = _create_payment(client, "a@example.com")
    second = _create_payment(client, "a@example.com")

    response = client.get("/payments")

    assert response.status_code == 200
    assert [item["id"] for item in response.json()] == [second, first]


def test_list_filters_by_email(client: TestClient) -> None:
    """GET /payments?email= отдаёт только платежи указанного email (бонус ТЗ)."""
    _create_payment(client, "a@example.com")
    target = _create_payment(client, "b@example.com")

    response = client.get("/payments", params={"email": "b@example.com"})

    assert response.status_code == 200
    assert [item["id"] for item in response.json()] == [target]


def test_list_filters_by_status(client: TestClient, session: Session) -> None:
    """GET /payments?status= отдаёт только платежи с указанным статусом (бонус ТЗ)."""
    pending = _create_payment(client, "a@example.com")
    refunded = _create_payment(client, "b@example.com")
    _set_status(session, refunded, "refunded")

    response = client.get("/payments", params={"status": "pending"})

    assert response.status_code == 200
    assert [item["id"] for item in response.json()] == [pending]


def test_list_applies_email_and_status_together(client: TestClient, session: Session) -> None:
    """Фильтры email и status применяются вместе (бонус ТЗ)."""
    _create_payment(client, "a@example.com")
    target = _create_payment(client, "a@example.com")
    _create_payment(client, "b@example.com")
    _set_status(session, target, "succeeded")

    response = client.get("/payments", params={"email": "a@example.com", "status": "succeeded"})

    assert response.status_code == 200
    assert [item["id"] for item in response.json()] == [target]
