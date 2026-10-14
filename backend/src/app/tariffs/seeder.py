"""Идемпотентный сид тарифов для старта приложения и тестов."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.tariffs.models import Tariff

TARIFF_SEEDS = (
    {"code": "basic", "title": "Basic", "price": 990000},
    {"code": "standard", "title": "Standard", "price": 1990000},
    {"code": "premium", "title": "Premium", "price": 2990000},
)


def seed_tariffs(session: Session) -> None:
    """Добавляет отсутствующие тарифы и не трогает уже существующие."""
    existing_codes = set(session.scalars(select(Tariff.code)))
    for seed in TARIFF_SEEDS:
        if seed["code"] not in existing_codes:
            session.add(Tariff(**seed))
    session.commit()
