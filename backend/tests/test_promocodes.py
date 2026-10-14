"""Тесты скидки по промокоду: чистая логика и API (ТЗ #1)."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.payments.models import Payment
from app.payments.promo import UnknownPromoCodeError, apply_promo


def test_without_promo_code_keeps_price() -> None:
    """Без промокода сумма равна цене, скидка 0."""
    assert apply_promo(1990000, None) == (1990000, 0)


def test_kvitto10_uppercase() -> None:
    """KVITTO10: standard дешевеет на 199000 копеек (ТЗ #1)."""
    assert apply_promo(1990000, "KVITTO10") == (1791000, 199000)


def test_kvitto10_mixed_case() -> None:
    """Промокод регистронезависим: kvitTo10 даёт ту же скидку."""
    assert apply_promo(1990000, "kvitTo10") == (1791000, 199000)


def test_kvitto10_lowercase_for_basic() -> None:
    """kvitto10 в нижнем регистре: скидка 10 % от цены Basic."""
    assert apply_promo(990000, "kvitto10") == (891000, 99000)


def test_unknown_promo_code_raises() -> None:
    """Неизвестный промокод поднимает UnknownPromoCodeError."""
    with pytest.raises(UnknownPromoCodeError):
        apply_promo(1990000, "SALE50")


def _payment_payload(**fields: object) -> dict[str, object]:
    """Собирает тело создания платежа, заменяя поля значениями из fields."""
    payload: dict[str, object] = {
        "tariff_id": 2,
        "email": "student@example.com",
        "method": "card",
    }
    payload.update(fields)
    return payload


def test_create_with_promo_code_discounts_response_and_db(
    client: TestClient, session: Session
) -> None:
    """KVITTO10: amount и discount из ТЗ #1 — и в ответе, и в базе."""
    response = client.post("/payments", json=_payment_payload(promo_code="KVITTO10"))

    assert response.status_code == 201
    body = response.json()
    assert body["amount"] == 1791000
    assert body["discount"] == 199000

    payment = session.get(Payment, body["id"])
    assert payment is not None
    assert (payment.amount, payment.discount) == (1791000, 199000)


def test_create_without_promo_code_keeps_full_price(client: TestClient, session: Session) -> None:
    """Без промокода amount равен цене тарифа, discount 0 — в ответе и в базе (ТЗ #1)."""
    response = client.post("/payments", json=_payment_payload())

    assert response.status_code == 201
    body = response.json()
    assert body["amount"] == 1990000
    assert body["discount"] == 0

    payment = session.get(Payment, body["id"])
    assert payment is not None
    assert (payment.amount, payment.discount) == (1990000, 0)


def test_create_with_lowercase_promo_code_discounts_same(
    client: TestClient, session: Session
) -> None:
    """Промокод в нижнем регистре даёт ту же скидку, что и в верхнем (ТЗ #1)."""
    response = client.post("/payments", json=_payment_payload(promo_code="kvitTo10"))

    assert response.status_code == 201
    body = response.json()
    assert body["amount"] == 1791000
    assert body["discount"] == 199000

    payment = session.get(Payment, body["id"])
    assert payment is not None
    assert (payment.amount, payment.discount) == (1791000, 199000)


def test_unknown_promo_code_is_rejected(client: TestClient) -> None:
    """Неизвестный промокод → 422 с detail по ТЗ (ТЗ #1)."""
    response = client.post("/payments", json=_payment_payload(promo_code="SALE50"))

    assert response.status_code == 422
    assert response.json() == {"detail": "unknown promo code"}


def test_unknown_tariff_id_is_rejected(client: TestClient) -> None:
    """Неизвестный tariff_id → 422 с detail по ТЗ."""
    response = client.post("/payments", json=_payment_payload(tariff_id=999))

    assert response.status_code == 422
    assert response.json() == {"detail": "unknown tariff"}
