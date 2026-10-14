"""HTTP-эндпоинты тарифов."""

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db import get_session
from app.tariffs.models import Tariff
from app.tariffs.repository import list_tariffs
from app.tariffs.schemas import TariffOut

router = APIRouter()


@router.get("/tariffs", response_model=list[TariffOut])
def get_tariffs(session: Annotated[Session, Depends(get_session)]) -> list[Tariff]:
    """Возвращает список тарифов с ценами в копейках."""
    return list_tariffs(session)
