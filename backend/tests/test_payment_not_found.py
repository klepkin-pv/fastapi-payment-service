"""Тесты GET /payments/{id}: 404 для неизвестного и точный состав полей (ТЗ #5)."""

from fastapi.testclient import TestClient

PAYMENT_FIELDS = frozenset(
    {
        "id",
        "status",
        "tariff_id",
        "amount",
        "discount",
        "method",
        "installment_months",
        "schedule",
        "email",
        "created_at",
    }
)


def test_unknown_payment_returns_404(client: TestClient) -> None:
    """GET /payments/999 → 404 с detail по ТЗ (ТЗ #5)."""
    response = client.get("/payments/999")

    assert response.status_code == 404
    assert response.json() == {"detail": "payment not found"}


def test_existing_payment_returns_exactly_spec_fields(client: TestClient) -> None:
    """GET созданного платежа → 200 и ровно поля объекта из ТЗ, без лишних (ТЗ #5)."""
    created = client.post(
        "/payments",
        json={"tariff_id": 1, "email": "student@example.com", "method": "card"},
    )
    assert created.status_code == 201

    response = client.get(f"/payments/{created.json()['id']}")

    assert response.status_code == 200
    body = response.json()
    assert set(body) == PAYMENT_FIELDS
    assert body["id"] == created.json()["id"]
    assert body["status"] == "pending"
