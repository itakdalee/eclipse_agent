"""
Конфигурация приложения.

Загружает переменные окружения и предоставляет типизированный доступ к настройкам.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Настройки приложения."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # OpenAI / OpenRouter настройки
    openai_api_key: str
    openai_base_url: str = "https://openrouter.ai/api/v1"
    model_name: str = "anthropic/claude-3.5-sonnet"

    # Секретное слово
    secret_word: str = "ECLIPSE2025"

    # Настройки приложения
    app_name: str = "Secret Word Challenge"
    debug: bool = False

    # CORS настройки
    cors_origins: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]


@lru_cache
def get_settings() -> Settings:
    """Получить singleton настроек приложения."""
    return Settings()
