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
cp .env.example .env            # при необходимости поправьте DATABASE_URL
createdb -U postgres payments   # один раз, если базы ещё нет
./local.run.ps1                 # Windows; ./local.run.sh — Linux и macOS
```

Скрипт накатывает миграции и поднимает сервер на http://localhost:8000.
Базу можно создать любым клиентом PostgreSQL: `createdb`, `psql -c "CREATE DATABASE payments"`, pgAdmin —
пользователь и пароль те же, что в `DATABASE_URL` (по умолчанию `postgres`).
Windows: если PowerShell блокирует скрипт, запусти `powershell -ExecutionPolicy Bypass -File .\local.run.ps1`.

## Тесты

```bash
cd backend && uv run pytest
```

## Примеры запросов

Swagger UI — http://localhost:8000/docs.

### Bash

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

### PowerShell

В Windows PowerShell `curl` — это алиас `Invoke-WebRequest` с другим синтаксисом, а `curl.exe` теряет кавычки при передаче тела с JSON, поэтому запросы отправляются через `Invoke-RestMethod`.

```powershell
Invoke-RestMethod http://localhost:8000/tariffs

Invoke-RestMethod -Uri http://localhost:8000/payments -Method Post -ContentType 'application/json' -Headers @{ 'Idempotency-Key' = 'demo-1' } -Body '{"tariff_id": 2, "email": "student@example.com", "method": "installment", "installment_months": 3, "promo_code": "KVITTO10"}'

$body = '{"payment_id": 1, "status": "succeeded"}'
$key = [Text.Encoding]::UTF8.GetBytes('dev-secret')
$data = [Text.Encoding]::UTF8.GetBytes($body)
$sig = [BitConverter]::ToString([Security.Cryptography.HMACSHA256]::new($key).ComputeHash($data)).Replace('-', '').ToLower()
Invoke-RestMethod -Uri http://localhost:8000/webhooks/bank -Method Post -ContentType 'application/json' -Headers @{ 'X-Signature' = $sig } -Body $body
```

Ошибки (401, 409, 422) `Invoke-RestMethod` показывает как исключение с кодом — это ожидаемо.
Примеры из блока Bash работают без изменений в Git Bash.

### Тела для Swagger

`POST /payments`:

```json
{
  "tariff_id": 2,
  "email": "student@example.com",
  "method": "installment",
  "installment_months": 3,
  "promo_code": "KVITTO10"
}
```

`POST /webhooks/bank` — заголовок `X-Signature` это hex-HMAC-SHA256 от того же тела с ключом `WEBHOOK_SECRET` (по умолчанию `dev-secret`):

```json
{
  "payment_id": 1,
  "status": "succeeded"
}
```

## Структура

`backend/` — сервис (FastAPI, SQLAlchemy, тесты), `database/` — миграции Alembic, `docker/` — образ и compose,
`local.run.*` — запуск без контейнеров. Правила работы ассистента — `AGENTS.md` и `.zcode/`.
