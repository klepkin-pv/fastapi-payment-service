"""График платежей при рассрочке."""

INSTALLMENT_MONTHS = frozenset({3, 6, 12})


def build_schedule(amount: int, months: int) -> list[int]:
    """Делит сумму на равные платежи, остаток добавляет к первым из них."""
    base_payment, remainder = divmod(amount, months)
    return [base_payment + 1 if index < remainder else base_payment for index in range(months)]
