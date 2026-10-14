"""Настройки приложения из переменных окружения и файла .env."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Параметры подключения к базе и проверки подписи вебхука."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str
    webhook_secret: str = ""


settings = Settings()
