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

        Raises:
            ValueError: При невалидных входных данных
        """
        messages: list[dict[str, Any]] = []

        # Добавляем системный промпт
        system_prompt = self.prompt_service.get_system_prompt()
        if not system_prompt or not system_prompt.strip():
            raise ValueError("System prompt cannot be empty")
        messages.append({"role": "system", "content": system_prompt})

        # Валидируем и добавляем историю разговора
        for i, msg in enumerate(conversation_history):
            if msg.role not in ("user", "assistant", "system"):
                raise ValueError(f"Message {i} in history: invalid role '{msg.role}'")
            if not msg.content or not msg.content.strip():
                raise ValueError(f"Message {i} in history: content cannot be empty")
            messages.append({"role": msg.role, "content": msg.content})

        # Валидируем текущее сообщение пользователя
        if not user_message or not user_message.strip():
            raise ValueError("User message cannot be empty")
        messages.append({"role": "user", "content": user_message})

        return messages

    def _validate_messages(self, messages: list[dict[str, Any]]) -> None:
        """
        Валидирует список сообщений перед отправкой в API.

        Args:
            messages: Список сообщений для валидации

        Raises:
            ValueError: Если сообщения невалидны
        """
        if not messages:
            raise ValueError("Список сообщений не может быть пустым")

        # Проверяем наличие обязательных ролей
        roles = [msg.get("role") for msg in messages]
        if "system" not in roles:
            raise ValueError("Отсутствует системный промпт")
        if "user" not in roles:
            raise ValueError("Отсутствует сообщение пользователя")

        # Проверяем структуру каждого сообщения
        for i, msg in enumerate(messages):
            if not isinstance(msg, dict):
                raise ValueError(f"Сообщение {i} должно быть словарем")

            if "role" not in msg or "content" not in msg:
                raise ValueError(f"Сообщение {i} должно содержать 'role' и 'content'")

            if msg["role"] not in ("system", "user", "assistant"):
                raise ValueError(f"Сообщение {i}: недопустимая роль '{msg['role']}'")

            if not isinstance(msg["content"], str):
                raise ValueError(f"Сообщение {i}: content должен быть строкой")

            if not msg["content"].strip():
                raise ValueError(f"Сообщение {i}: content не может быть пустым")

        logger.debug(f"Валидация пройдена: {len(messages)} сообщений")

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
            ValueError: При невалидных входных данных
            OpenAIError: При ошибке API после всех попыток
        """
        # Формируем список сообщений для API
        messages = self._build_messages(user_message, conversation_history)

        # Валидируем перед отправкой
        self._validate_messages(messages)

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

                # Валидация структуры ответа
                if not response.choices:
                    raise ValueError("API returned no choices")

                message = response.choices[0].message
                if not hasattr(message, 'content'):
                    raise ValueError("API response missing content field")

                assistant_message = message.content

                # Валидация содержимого ответа
                if assistant_message is None or not assistant_message.strip():
                    raise ValueError("API returned empty or whitespace-only response")

                if len(assistant_message.strip()) <= 1:
                    raise ValueError("API returned suspiciously short response")

                logger.info("Успешно получен ответ от API")
                return assistant_message

            except (OpenAIError, ValueError, Exception) as e:
                last_error = e
                error_type = type(e).__name__

                # Не повторяем запрос при ошибках валидации
                if isinstance(e, ValueError):
                    logger.error(f"Ошибка валидации ответа: {e}")
                    raise last_error

                # Retry logic для сетевых и API ошибок
                if attempt < self.max_retries_on_error:
                    wait_time = 2 ** attempt  # Exponential backoff: 1, 2, 4 секунды
                    logger.warning(
                        f"{error_type} (попытка {attempt + 1}/{self.max_retries_on_error + 1}): "
                        f"{e}. Повтор через {wait_time}с"
                    )
                    await sleep(wait_time)
                else:
                    logger.error(
                        f"Ошибка после {self.max_retries_on_error + 1} попыток. "
                        f"Последняя ошибка: {error_type}: {e}"
                    )
                    raise last_error

        # Safety net (недостижимый код, но на всякий случай)
        if last_error:
            raise last_error
        raise OpenAIError(f"Failed after {self.max_retries_on_error + 1} attempts")

    async def health_check(self) -> bool:
        """
        Проверяет доступность API.

        Returns:
            True если API доступен, False в противном случае
        """
        try:
            # Минимальный тестовый запрос
            # Используем chat completion вместо models.list()
            # так как не все провайдеры поддерживают список моделей
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "health check"}],
                max_tokens=5,
            )

            # Проверяем, что получили валидный ответ
            return response is not None and len(response.choices) > 0

        except Exception as e:
            logger.error(f"Health check failed: {type(e).__name__}: {e}")
            return False