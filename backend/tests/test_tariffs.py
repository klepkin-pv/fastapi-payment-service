"""Тесты эндпоинта тарифов и идемпотентного сида (ТЗ #1)."""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.tariffs.repository import list_tariffs
from app.tariffs.seeder import seed_tariffs


def test_get_tariffs_returns_three_tariffs(client: TestClient) -> None:
    """GET /tariffs отдаёт три тарифа с точными ценами и полями id/title/price."""
    response = client.get("/tariffs")

    assert response.status_code == 200
    assert response.json() == [
        {"id": 1, "title": "Basic", "price": 990000},
        {"id": 2, "title": "Standard", "price": 1990000},
        {"id": 3, "title": "Premium", "price": 2990000},
    ]


def test_seed_tariffs_is_idempotent(session: Session) -> None:
    """Повторный сид не создаёт дубликатов тарифов."""
    seed_tariffs(session)
    seed_tariffs(session)

    assert len(list_tariffs(session)) == 3
