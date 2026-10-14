"""Проверка подписи вебхука банка."""

import hashlib
import hmac


class InvalidSignatureError(Exception):
    """Подпись запроса отсутствует или не совпадает с ожидаемой."""


def verify_signature(raw_body: bytes, signature: str | None, secret: str) -> bool:
    """Сверяет hex-HMAC-SHA256 подписи тела запроса с ожидаемой."""
    if not signature or not secret:
        return False

    expected = hmac.new(secret.encode(), raw_body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)
