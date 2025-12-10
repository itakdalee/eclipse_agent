"""
Сервис для работы с OpenAI API.

Управляет взаимодействием с OpenAI-совместимыми API (OpenRouter, OpenAI и др.)
"""

import logging
from typing import Any
from asyncio import sleep

from openai import AsyncOpenAI, OpenAIError

from app.config import Settings
from app.models import Message
from app.services.prompt_service import PromptService

logger = logging.getLogger(__name__)


class OpenAIService:
    """Сервис для отправки запросов к OpenAI API."""
    max_retries_on_error = 3

    def __init__(self, settings: Settings, prompt_service: PromptService) -> None:
        """
        Инициализация сервиса.

        Args:
            settings: Настройки приложения
            prompt_service: Сервис управления промптами
        """
        self.settings = settings
        self.prompt_service = prompt_service

        # Инициализация асинхронного клиента OpenAI
        self.client = AsyncOpenAI(
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
        )

        self.model = settings.model_name

    async def send_message(
        self, user_message: str, conversation_history: list[Message]
    ) -> str:
        """
        Отправляет сообщение в OpenAI API и возвращает ответ.

        Args:
            user_message: Сообщение от пользователя
            conversation_history: История разговора

        Returns:
            Ответ от AI

        Raises:
            OpenAIError: При ошибке API после всех попыток
        """
        # Формируем список сообщений для API
        messages = self._build_messages(user_message, conversation_history)

        last_error = None

        for attempt in range(self.max_retries_on_error + 1):
            try:
                logger.info(f"Отправка запроса к {self.model} (попытка {attempt + 1})")

                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    max_tokens=1024,
                    temperature=0.44,
                    top_p=0.9,
                    frequency_penalty=0.3,
                )

                assistant_message = response.choices[0].message.content

                # Проверка на корректность ответа
                if assistant_message is None or not assistant_message.strip() or len(assistant_message.strip()) <= 1:
                    logger.warning(f"Получен некорректный ответ от API (попытка {attempt + 1}): пустой или слишком короткий")
                    # Если получен некорректный ответ - бросаем исключение для retry
                    raise OpenAIError("Empty or invalid response from API")

                logger.info("Успешно получен ответ от API")
                return assistant_message

            except OpenAIError as e:
                last_error = e
                if attempt < self.max_retries_on_error:
                    wait_time = 2 ** attempt  # Exponential backoff: 1, 2, 4 секунды
                    logger.warning(f"Ошибка OpenAI API (попытка {attempt + 1}/{self.max_retries_on_error + 1}): {e}. Повтор через {wait_time}с")
                    await sleep(wait_time)
                else:
                    logger.error(f"Ошибка OpenAI API после {self.max_retries_on_error + 1} попыток: {e}")
                    raise last_error

        # На случай, если цикл завершился без return (не должно происходить)
        raise OpenAIError(f"Failed after {self.max_retries_on_error + 1} attempts")

    def _build_messages(
        self, user_message: str, conversation_history: list[Message]
    ) -> list[dict[str, Any]]:
        """
        Строит список сообщений для отправки в API.

        Args:
            user_message: Текущее сообщение пользователя
            conversation_history: История разговора

        Returns:
            Список сообщений в формате OpenAI API
        """
        messages: list[dict[str, Any]] = []

        # Добавляем системный промпт
        system_prompt = self.prompt_service.get_system_prompt()
        messages.append({"role": "system", "content": system_prompt})

        # Добавляем историю разговора (без системных сообщений и пустых content)
        for msg in conversation_history:
            if msg.role in ("user", "assistant") and msg.content and msg.content.strip():
                messages.append({"role": msg.role, "content": msg.content})

        # Добавляем текущее сообщение пользователя
        messages.append({"role": "user", "content": user_message})

        return messages

    async def health_check(self) -> bool:
        """
        Проверяет доступность API.

        Returns:
            True если API доступен
        """
        try:
            # Простой тестовый запрос
            await self.client.models.list()
            return True
        except OpenAIError:
            return False
