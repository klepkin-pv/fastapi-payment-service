"""Тесты проверки подписи X-Signature на вебхуке банка (бонус ТЗ)."""

import hashlib
import hmac
import json

from fastapi.testclient import TestClient

WEBHOOK_SECRET = "test-secret"
INVALID_JSON = b'{"payment_id": 1,'


def _sign(body: bytes) -> str:
    """Считает подпись вебхука — hex-HMAC-SHA256 от точного тела запроса."""
    return hmac.new(WEBHOOK_SECRET.encode(), body, hashlib.sha256).hexdigest()


def _body(payment_id: int, status: str) -> bytes:
    """Собирает сырое тело вебхука."""
    return json.dumps({"payment_id": payment_id, "status": status}).encode()


def _create_payment(client: TestClient) -> int:
    """Создаёт платёж и возвращает его идентификатор."""
    response = client.post(
        "/payments",
        json={"tariff_id": 2, "email": "student@example.com", "method": "card"},
    )
    assert response.status_code == 201
    return response.json()["id"]


def test_valid_signature_is_accepted(client: TestClient) -> None:
    """Корректная подпись тела → 200 {"result": "ok"}."""
    body = _body(_create_payment(client), "succeeded")

    response = client.post(
        "/webhooks/bank",
        content=body,
        headers={"Content-Type": "application/json", "X-Signature": _sign(body)},
    )

    assert response.status_code == 200
    assert response.json() == {"result": "ok"}


def test_missing_signature_is_rejected(client: TestClient) -> None:
    """Без заголовка X-Signature → 401 с detail по ТЗ."""
    response = client.post(
        "/webhooks/bank",
        content=_body(_create_payment(client), "succeeded"),
        headers={"Content-Type": "application/json"},
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "invalid signature"}


def test_wrong_signature_is_rejected(client: TestClient) -> None:
    """Подпись от другого тела → 401."""
    payment_id = _create_payment(client)
    body = _body(payment_id, "succeeded")

    response = client.post(
        "/webhooks/bank",
        content=body,
        headers={
            "Content-Type": "application/json",
            "X-Signature": _sign(_body(payment_id, "refunded")),
        },
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "invalid signature"}


def test_signature_checked_before_payment_lookup(client: TestClient) -> None:
    """Без подписи несуществующий платёж даёт 401, а не 404: подпись проверяется раньше."""
    response = client.post(
        "/webhooks/bank",
        content=_body(999, "succeeded"),
        headers={"Content-Type": "application/json"},
    )

    assert response.status_code == 401


def test_signature_checked_before_body_validation(client: TestClient) -> None:
    """Неверная подпись отсекается до проверки тела: 401, а не 422."""
    body = b'{"payment_id": "not-an-int", "status": "cancelled"}'

    response = client.post(
        "/webhooks/bank",
        content=body,
        headers={"Content-Type": "application/json", "X-Signature": "deadbeef"},
    )

    assert response.status_code == 401


def test_invalid_json_without_signature_is_rejected(client: TestClient) -> None:
    """Битый JSON без подписи → 401: подпись проверяется раньше разбора тела."""
    response = client.post(
        "/webhooks/bank",
        content=INVALID_JSON,
        headers={"Content-Type": "application/json"},
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "invalid signature"}


def test_invalid_json_with_valid_signature_is_validation_error(client: TestClient) -> None:
    """Битый JSON с корректной подписью → 422 стандартного формата FastAPI."""
    response = client.post(
        "/webhooks/bank",
        content=INVALID_JSON,
        headers={"Content-Type": "application/json", "X-Signature": _sign(INVALID_JSON)},
    )

    assert response.status_code == 422
    assert "detail" in response.json()
