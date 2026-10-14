"""Сквозной сценарий оплаты: тарифы, промокод, рассрочка, повторы и статусы."""

import hashlib
import hmac
import json

import httpx
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.payments.models import Payment

WEBHOOK_SECRET = "test-secret"


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


def test_full_payment_flow(client: TestClient, session: Session) -> None:
    """Тарифы → платёж с промокодом и рассрочкой → идемпотентный повтор → статусы."""
    tariffs = client.get("/tariffs")

    assert tariffs.status_code == 200
    assert [tariff["id"] for tariff in tariffs.json()] == [1, 2, 3]
    tariff_id = tariffs.json()[1]["id"]

    payload = {
        "tariff_id": tariff_id,
        "email": "student@example.com",
        "method": "installment",
        "installment_months": 6,
        "promo_code": "STUDY10",
    }
    created = client.post("/payments", json=payload, headers={"Idempotency-Key": "e2e-1"})

    assert created.status_code == 201
    body = created.json()
    assert body["amount"] == 1791000
    assert body["discount"] == 199000
    assert body["schedule"] == [298500] * 6
    assert sum(body["schedule"]) == body["amount"]

    repeated = client.post("/payments", json=payload, headers={"Idempotency-Key": "e2e-1"})

    assert repeated.status_code == 200
    assert repeated.json()["id"] == body["id"]
    assert session.scalar(select(func.count(Payment.id))) == 1

    succeeded = _send_webhook(client, body["id"], "succeeded")

    assert succeeded.status_code == 200
    assert succeeded.json() == {"result": "ok"}

    repeated_succeeded = _send_webhook(client, body["id"], "succeeded")

    assert repeated_succeeded.status_code == 409
    assert repeated_succeeded.json() == {"error": "invalid_transition"}
    assert _db_status(session, body["id"]) == "succeeded"

    refunded = _send_webhook(client, body["id"], "refunded")

    assert refunded.status_code == 200
    assert refunded.json() == {"result": "ok"}
    assert _db_status(session, body["id"]) == "refunded"
