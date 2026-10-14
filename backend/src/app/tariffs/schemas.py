"""Схемы ответов по тарифам."""

from pydantic import BaseModel, ConfigDict


class TariffOut(BaseModel):
    """Тариф в ответе API: идентификатор, название и цена в копейках."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    price: int
