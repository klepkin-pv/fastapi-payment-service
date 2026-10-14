# API платежей

FastAPI-сервис приёма оплаты курса: тарифы, платёж с промокодом и рассрочкой, статусы
`pending → succeeded/failed → refunded` и вебхук банка с проверкой подписи. Все суммы — целые копейки.

## Запуск в контейнерах

```bash
docker compose -f docker/docker-compose.prod.yml up --build
```

API — http://localhost:8000. Контейнер `migrations` применяет схему до старта API.
Без настройки подставляются пользователь и база `payments`, секрет вебхука `dev-secret`; свои значения — в `.env` в корне (шаблон — `.env.example`):

```bash
docker compose --env-file .env -f docker/docker-compose.prod.yml up --build
```

## Локальный запуск

Нужны Python 3.14, [uv](https://docs.astral.sh/uv/) и PostgreSQL.

```bash
cp .env.example .env    # при необходимости поправьте DATABASE_URL
createdb payments       # один раз, если базы ещё нет
./local.run.ps1         # Windows; ./local.run.sh — Linux и macOS
```

Скрипт накатывает миграции и поднимает сервер на http://localhost:8000.
Базу можно создать любым клиентом PostgreSQL: `createdb`, `psql -c "CREATE DATABASE payments"`, pgAdmin.

## Тесты

```bash
cd backend && uv run pytest
```

## Примеры запросов

```bash
curl -s http://localhost:8000/tariffs

curl -s -X POST http://localhost:8000/payments \
  -H 'Content-Type: application/json' -H 'Idempotency-Key: demo-1' \
  -d '{"tariff_id": 2, "email": "student@example.com", "method": "installment", "installment_months": 3, "promo_code": "KVITTO10"}'

curl -s http://localhost:8000/payments/1
curl -s "http://localhost:8000/payments?status=pending&email=student@example.com"

BODY='{"payment_id": 1, "status": "succeeded"}'
SIG=$(printf '%s' "$BODY" | python -c "import sys,hmac,hashlib;print(hmac.new(b'dev-secret',sys.stdin.buffer.read(),hashlib.sha256).hexdigest())")
curl -s -X POST http://localhost:8000/webhooks/bank \
  -H 'Content-Type: application/json' -H "X-Signature: $SIG" -d "$BODY"
```

## Структура

`backend/` — сервис (FastAPI, SQLAlchemy, тесты), `database/` — миграции Alembic, `docker/` — образ и compose,
`local.run.*` — запуск без контейнеров. Правила работы ассистента — `AGENTS.md` и `.zcode/`.
