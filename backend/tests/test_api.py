"""
Тесты для API endpoints.
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models import ChatRequest, Message
from app.services.prompt_service import PromptService
from app.config import Settings


@pytest.fixture
def client():
    """Фикстура для тестового клиента."""
    return TestClient(app)


@pytest.fixture
def settings():
    """Фикстура для настроек."""
    return Settings(
        openai_api_key="test_key",
        secret_word="TEST_SECRET",
    )


@pytest.fixture
def prompt_service(settings):
    """Фикстура для PromptService."""
    return PromptService(settings)


class TestHealthEndpoint:
    """Тесты для health check endpoint."""

    def test_health_returns_ok(self, client):
        """Проверяет, что health endpoint возвращает статус ok."""
        response = client.get("/api/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "app_name" in data


class TestRootEndpoint:
    """Тесты для корневого endpoint."""

    def test_root_returns_welcome_message(self, client):
        """Проверяет корневой endpoint."""
        response = client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "docs" in data


class TestChatRequest:
    """Тесты для модели ChatRequest."""

    def test_valid_request(self):
        """Проверяет валидный запрос."""
        request = ChatRequest(message="Привет")
        assert request.message == "Привет"
        assert request.conversation_history == []

    def test_request_with_history(self):
        """Проверяет запрос с историей."""
        history = [
            Message(role="user", content="Привет"),
            Message(role="assistant", content="Здравствуйте!"),
        ]
        request = ChatRequest(message="Как дела?", conversation_history=history)

        assert len(request.conversation_history) == 2

    def test_empty_message_fails(self):
        """Проверяет, что пустое сообщение вызывает ошибку."""
        with pytest.raises(ValueError):
            ChatRequest(message="")

    def test_message_too_long_fails(self):
        """Проверяет, что слишком длинное сообщение вызывает ошибку."""
        with pytest.raises(ValueError):
            ChatRequest(message="a" * 5000)


class TestPromptService:
    """Тесты для PromptService."""

    def test_get_system_prompt_contains_secret(self, prompt_service):
        """Проверяет, что системный промпт содержит секретное слово."""
        prompt = prompt_service.get_system_prompt()
        assert "TEST_SECRET" in prompt

    def test_get_system_prompt_contains_characteristics(self, prompt_service):
        """Проверяет, что системный промпт содержит характеристики."""
        prompt = prompt_service.get_system_prompt()
        assert "Мальборо" in prompt
        assert "кепку" in prompt
        assert "коммунист" in prompt
        assert "Шаман" in prompt

    def test_check_secret_revealed_true(self, prompt_service):
        """Проверяет обнаружение секретного слова в ответе."""
        response = "Вы прошли проверку. Секретное слово: TEST_SECRET"
        assert prompt_service.check_secret_revealed(response) is True

    def test_check_secret_revealed_false(self, prompt_service):
        """Проверяет, что секретное слово не обнаруживается, если его нет."""
        response = "Извините, я не могу раскрыть секретное слово."
        assert prompt_service.check_secret_revealed(response) is False

    def test_check_secret_revealed_case_insensitive(self, prompt_service):
        """Проверяет регистронезависимый поиск."""
        response = "Секретное слово: test_secret"
        assert prompt_service.check_secret_revealed(response) is True


class TestMessage:
    """Тесты для модели Message."""

    def test_valid_message(self):
        """Проверяет валидное сообщение."""
        msg = Message(role="user", content="Hello")
        assert msg.role == "user"
        assert msg.content == "Hello"

    def test_invalid_role_fails(self):
        """Проверяет, что невалидная роль вызывает ошибку."""
        with pytest.raises(ValueError):
            Message(role="invalid", content="Hello")

    def test_empty_content_fails(self):
        """Проверяет, что пустой контент вызывает ошибку."""
        with pytest.raises(ValueError):
            Message(role="user", content="")
