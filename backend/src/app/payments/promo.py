"""Промокоды: расчёт скидки к цене тарифа."""

PROMO_DISCOUNTS = {"STUDY10": 10}


class UnknownPromoCodeError(Exception):
    """Промокод не найден среди действующих."""


def apply_promo(price: int, promo_code: str | None) -> tuple[int, int]:
    """Возвращает сумму к оплате и скидку в копейках для промокода."""
    if promo_code is None:
        return price, 0

    discount_percent = PROMO_DISCOUNTS.get(promo_code.upper())
    if discount_percent is None:
        raise UnknownPromoCodeError(promo_code)

    discount = price * discount_percent // 100
    return price - discount, discount
