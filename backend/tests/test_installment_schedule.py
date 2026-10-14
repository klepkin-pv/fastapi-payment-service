"""Тесты графика рассрочки: чистая логика и API (ТЗ #2)."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.payments.models import Payment
from app.payments.schedule import build_schedule


def test_schedule_matches_spec_example() -> None:
    """1990000 на 3 месяца — [663334, 663333, 663333] (ТЗ #1)."""
    assert build_schedule(1990000, 3) == [663334, 663333, 663333]


@pytest.mark.parametrize("months", [3, 6, 12])
def test_schedule_has_installment_months_payments(months: int) -> None:
    """Число платежей равно сроку рассрочки, их сумма — исходной сумме."""
    schedule = build_schedule(1990000, months)

    assert len(schedule) == months
    assert sum(schedule) == 1990000


def test_remainder_goes_to_first_payments() -> None:
    """Неделимая сумма: остаток от деления уходит в первые платежи."""
    assert build_schedule(100, 3) == [34, 33, 33]


def test_even_split_has_no_remainder() -> None:
    """Делимая сумма раскладывается поровну."""
    assert build_schedule(1200, 12) == [100] * 12


@pytest.mark.parametrize("months", [3, 6, 12])
def test_installment_schedule_covers_amount(
    client: TestClient, session: Session, months: int
) -> None:
    """График на 3/6/12 месяцев даёт сумму, равную amount в ответе и в базе (ТЗ #2)."""
    response = client.post(
        "/payments",
        json={
            "tariff_id": 2,
            "email": "student@example.com",
            "method": "installment",
            "installment_months": months,
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["installment_months"] == months
    assert len(body["schedule"]) == months
    assert sum(body["schedule"]) == body["amount"]

    payment = session.get(Payment, body["id"])
    assert payment is not None
    assert payment.amount == body["amount"]


def test_spec_example_standard_three_months(client: TestClient) -> None:
    """Пример ТЗ #2: standard на 3 месяца — amount 1990000 и [663334, 663333, 663333]."""
    response = client.post(
        "/payments",
        json={
            "tariff_id": 2,
            "email": "student@example.com",
            "method": "installment",
            "installment_months": 3,
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["amount"] == 1990000
    assert body["schedule"] == [663334, 663333, 663333]


@pytest.mark.parametrize("method", ["card", "sbp"])
def test_non_installment_methods_have_no_schedule(
    client: TestClient, session: Session, method: str
) -> None:
    """card/sbp: месяцы отбрасываются, schedule и installment_months — null (ТЗ #2)."""
    response = client.post(
        "/payments",
        json={
            "tariff_id": 2,
            "email": "student@example.com",
            "method": method,
            "installment_months": 6,
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["installment_months"] is None
    assert body["schedule"] is None

    payment = session.get(Payment, body["id"])
    assert payment is not None
    assert payment.installment_months is None


def test_installment_without_months_is_rejected(client: TestClient) -> None:
    """Рассрочка без installment_months → 422 (ТЗ #2)."""
    response = client.post(
        "/payments",
        json={"tariff_id": 2, "email": "student@example.com", "method": "installment"},
    )

    assert response.status_code == 422


def test_installment_with_unsupported_months_is_rejected(client: TestClient) -> None:
    """Рассрочка на 5 месяцев → 422: допустимы только 3, 6 и 12 (ТЗ #2)."""
    response = client.post(
        "/payments",
        json={
            "tariff_id": 2,
            "email": "student@example.com",
            "method": "installment",
            "installment_months": 5,
        },
    )

    assert response.status_code == 422
