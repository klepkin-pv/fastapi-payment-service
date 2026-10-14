"""Запросы к таблице тарифов."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.tariffs.models import Tariff


class UnknownTariffError(Exception):
    """Тариф с указанным идентификатором не найден."""


def list_tariffs(session: Session) -> list[Tariff]:
    """Возвращает тарифы, отсортированные по возрастанию id."""
    return list(session.scalars(select(Tariff).order_by(Tariff.id)))


def get_tariff(session: Session, tariff_id: int) -> Tariff | None:
    """Возвращает тариф по идентификатору или None."""
    return session.get(Tariff, tariff_id)
