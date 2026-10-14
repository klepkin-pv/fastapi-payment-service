"""Модель тарифа."""

from sqlalchemy import CheckConstraint, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class Tariff(Base):
    """Тариф курса с ценой в копейках."""

    __tablename__ = "tariffs"
    __table_args__ = (CheckConstraint("price > 0", name="price_positive"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(32), nullable=False, unique=True)
    title: Mapped[str] = mapped_column(String(64), nullable=False)
    price: Mapped[int] = mapped_column(nullable=False)
