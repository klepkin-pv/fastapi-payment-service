# Working Context

> Память проекта между сессиями. Агент читает этот файл в начале каждой сессии.
> Держи его коротким: он грузится в контекст всегда.

---

## Проект

**Название:** fastapi-payment-service
**Описание:** Сервис приёма платежей онлайн-школы: тарифы, платёж с промокодом и рассрочкой, статусная машина, вебхук банка.
**Пользователи:** плательщик — студент онлайн-школы; проверяющий — CTO компании, созвон с разбором кода
**Начат:** 2026-10-14

---

## Стек (инвариант)

| Слой | Выбор |
|------|-------|
| Язык | Python 3.14 (`requires-python = ">=3.11"`) |
| Фронтенд | нет (ТЗ: «фронтенд не нужен»), `frontend/` не создаётся |
| Бэкенд | FastAPI + Pydantic v2, uvicorn |
| База данных | PostgreSQL 18 (compose и локально); SQLite in-memory — только тесты |
| ORM / доступ к данным | SQLAlchemy 2.x (синхронный), драйвер psycopg 3 |
| Миграции | Alembic, конфиг и версии — в `database/` |
| Менеджер зависимостей | uv 0.13 (`backend/pyproject.toml` + `backend/uv.lock`) |
| Тесты | pytest + httpx TestClient, SQLite in-memory (StaticPool); 68 тестов |
| Линтер / форматтер | ruff (check + format), pre-commit |
| Сборка и запуск | docker compose (`docker/docker-compose.prod.yml`, контейнер миграций); без Docker — `local.run.sh` / `local.run.ps1` на локальном PostgreSQL |

---

## Раскладка

**Сервисы:**
- `backend/` — единственный сервис (API): свой `pyproject.toml`, `uv.lock`, тесты в `backend/tests/`, код в `backend/src/app/` по фичам (tariffs, payments, webhooks, core)
- `database/` — Alembic: `alembic.ini`, `migrations/env.py`, `versions/0001_create_tariffs_and_payments.py`
- `docker/` — `Dockerfile`, `docker-compose.prod.yml`, `migrate.sh`, `entrypoint.sh`
- `frontend/` не создаётся

**Локальный запуск:**
- Контейнеры: `docker compose -f docker/docker-compose.prod.yml up --build` (db → migrations → api; свои настройки — `--env-file .env`)
- Без Docker: `cp .env.example .env`, `createdb payments`, `./local.run.ps1` (или `./local.run.sh`) — скрипт накатывает миграции и поднимает uvicorn

**Отличия от Docker:** тесты идут на SQLite in-memory вместо PostgreSQL — внешние сервисы не нужны ни локально, ни в CI; отличается только фикстура тестов и дефолт `DATABASE_URL` при запуске без `.env`. Бизнес-логика, запросы и миграции общие

---

## Режим работы

**Команда:** solo
**Git режим:** solo (коммиты в основную ветку)
**TDD при фиксах:** включён
**Учёт расходов:** отключён (`cost_tracker_on` убран из AGENTS.md, хук не зарегистрирован)

---

## Текущий статус

**Обновлено:** 2026-10-14
**Текущая задача:** проект собран целиком — план `.plans/2026-10-14-payments-api.md`, все 15 задач закрыты
**Следующий шаг:** публикация репозитория на GitHub за заказчиком (push по явной просьбе); на созвоне — `helper.md` с вопросами и ответами
**Известные проблемы:**
- GitHub Actions локально не запускается: workflow проверен глазами, те же команды прогнаны вручную
- `local.run.ps1` (Windows-двойник `local.run.sh`) синтаксически проверен, но не исполнялся — прогнан `.sh`

**Проверено на машине заказчика:** 68 тестов зелёные, ruff и pre-commit чистые, миграции на PostgreSQL 18.6 и SQLite, `docker compose ... up --build` (migrations Exited(0) → api healthy), сценарии ТЗ прогнаны curl и в контейнере, и на локальном сервере

---

## Что неочевидно для нового агента

- Комментарии в коде запрещены, только докстринги; идентификаторы английские, докстринги/README/AI_LOG.md/helper.md — русский
- Все суммы — только `int` в копейках; `float`/`Decimal`/`Numeric` в деньгах запрещены (ТЗ)
- Коды и тела ответов — строго по ТЗ: `{"error": "invalid_transition"}` (409), `{"result": "ok"}` (200), 404, 422 стандартного формата FastAPI; своих форматов не вводить
- `DATABASE_URL` обязателен (нет дефолта) — молчаливый откат к SQLite запрещён; `WEBHOOK_SECRET` обязателен на старте приложения
- Подпись вебхука проверяется до разбора тела и до поиска платежа; пустой секрет означает «подпись не проходит» (fail-closed)
- `Idempotency-Key` длиннее 255 символов отклоняется с 422 (совпадает с ограничением столбца)
- `helper.md` (вопросы и ответы для созвона с CTO) в `.gitignore` и `.dockerignore` — в репозиторий и в образ не попадает
- `.zcode` отфильтрован для сдачи: в репозитории 6 ролей, 3 правила, 2 скилла; `vision`, `qa`, `graphify`, примеры конфигов MCP и cost-tracker остались только локально (перечислены в `.gitignore`)
