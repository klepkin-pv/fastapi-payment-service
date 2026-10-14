"""Общие фикстуры тестов: окружение, база в памяти, клиент приложения."""

import os
from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

os.environ.setdefault("WEBHOOK_SECRET", "test-secret")
os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite://")

from app.core.db import Base, get_session
from app.main import app
from app.tariffs.seeder import seed_tariffs


@pytest.fixture
def engine() -> Iterator[Engine]:
    """Создаёт SQLite в памяти с таблицами моделей на время одного теста."""
    test_engine = create_engine(
        "sqlite+pysqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(test_engine)
    yield test_engine
    test_engine.dispose()


@pytest.fixture
def session(engine: Engine) -> Iterator[Session]:
    """Отдаёт сессию, привязанную к тестовой базе."""
    factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    with factory() as test_session:
        yield test_session


@pytest.fixture
def client(session: Session) -> Iterator[TestClient]:
    """Отдаёт клиент с подменённой сессией и засеянными тарифами."""
    seed_tariffs(session)
    app.dependency_overrides[get_session] = lambda: session
    yield TestClient(app)
    app.dependency_overrides.clear()
