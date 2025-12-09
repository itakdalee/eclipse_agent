"""
Pydantic модели для API.

Определяет структуры данных для запросов и ответов.
"""

from pydantic import BaseModel, Field


class Message(BaseModel):
    """Сообщение в истории разговора."""

    role: str = Field(
        ...,
        description="Роль отправителя сообщения",
        pattern="^(user|assistant|system)$",
    )
    content: str = Field(..., description="Содержимое сообщения", min_length=1)


class ChatRequest(BaseModel):
    """Запрос на отправку сообщения в чат."""

    message: str = Field(
        ..., description="Сообщение пользователя", min_length=1, max_length=4000
    )
    conversation_history: list[Message] = Field(
        default_factory=list, description="История разговора"
    )


class ChatResponse(BaseModel):
    """Ответ от AI."""

    response: str = Field(..., description="Ответ от AI")
    is_secret_revealed: bool = Field(
        default=False, description="Флаг, указывающий было ли раскрыто секретное слово"
    )


class HealthResponse(BaseModel):
    """Ответ health check."""

    status: str = Field(default="ok", description="Статус сервера")
    app_name: str = Field(..., description="Название приложения")


class ErrorResponse(BaseModel):
    """Ответ с ошибкой."""

    detail: str = Field(..., description="Описание ошибки")
