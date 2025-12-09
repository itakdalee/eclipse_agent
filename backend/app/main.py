"""
Secret Word Challenge - FastAPI Application.

Главный модуль приложения. Инициализирует FastAPI и подключает маршруты.
"""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.config import get_settings

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Lifecycle менеджер приложения."""
    settings = get_settings()
    logger.info(f"Запуск приложения: {settings.app_name}")
    logger.info(f"Используемая модель: {settings.model_name}")
    logger.info(f"Base URL: {settings.openai_base_url}")
    yield
    logger.info("Завершение работы приложения")


def create_app() -> FastAPI:
    """Фабрика для создания FastAPI приложения."""
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        description="Интерактивная игра, где пользователи должны узнать у AI секретное слово",
        version="1.0.0",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # Настройка CORS для фронтенда
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Подключение маршрутов
    app.include_router(router)

    return app


# Создаём экземпляр приложения
app = create_app()


@app.get("/", include_in_schema=False)
async def root() -> dict[str, str]:
    """Корневой endpoint - редирект на документацию."""
    return {
        "message": "Welcome to Secret Word Challenge API",
        "docs": "/docs",
        "health": "/api/health",
    }
