"""
API маршруты приложения.

Определяет endpoints для работы с чатом.
"""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from openai import OpenAIError

from app.config import Settings, get_settings
from app.models import ChatRequest, ChatResponse, ErrorResponse, HealthResponse
from app.services.openai_service import OpenAIService
from app.services.prompt_service import PromptService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["chat"])


def get_prompt_service(
    settings: Annotated[Settings, Depends(get_settings)],
) -> PromptService:
    """Dependency для получения PromptService."""
    return PromptService(settings)


def get_openai_service(
    settings: Annotated[Settings, Depends(get_settings)],
    prompt_service: Annotated[PromptService, Depends(get_prompt_service)],
) -> OpenAIService:
    """Dependency для получения OpenAIService."""
    return OpenAIService(settings, prompt_service)


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Проверка статуса сервера",
    description="Возвращает статус работы сервера",
)
async def health_check(
    settings: Annotated[Settings, Depends(get_settings)],
) -> HealthResponse:
    """Health check endpoint."""
    return HealthResponse(status="ok", app_name=settings.app_name)


@router.post(
    "/chat",
    response_model=ChatResponse,
    responses={
        500: {"model": ErrorResponse, "description": "Ошибка сервера"},
        503: {"model": ErrorResponse, "description": "Сервис недоступен"},
    },
    summary="Отправить сообщение в чат",
    description="Отправляет сообщение пользователя AI и возвращает ответ",
)
async def chat(
    request: ChatRequest,
    openai_service: Annotated[OpenAIService, Depends(get_openai_service)],
    prompt_service: Annotated[PromptService, Depends(get_prompt_service)],
) -> ChatResponse:
    """
    Основной endpoint для общения с AI.

    Принимает сообщение пользователя и историю разговора,
    отправляет запрос в OpenAI API и возвращает ответ.
    """
    logger.info(f"Получено сообщение: {request.message[:50]}...")

    try:
        response = await openai_service.send_message(
            user_message=request.message,
            conversation_history=request.conversation_history,
        )

        # Проверяем, было ли раскрыто секретное слово
        is_secret_revealed = prompt_service.check_secret_revealed(response)

        if is_secret_revealed:
            logger.info("Секретное слово было раскрыто!")

        return ChatResponse(response=response, is_secret_revealed=is_secret_revealed)

    except OpenAIError as e:
        logger.error(f"Ошибка OpenAI API: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Сервис AI временно недоступен. Попробуйте позже.",
        ) from e

    except Exception as e:
        logger.exception(f"Неожиданная ошибка: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Произошла внутренняя ошибка сервера.",
        ) from e
