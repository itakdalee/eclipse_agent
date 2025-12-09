FROM python:3.13-slim

WORKDIR /app

# Копируем файлы зависимостей
COPY pyproject.toml README.md ./

# Копируем код приложения
COPY app ./app

# Устанавливаем зависимости
RUN pip install --no-cache-dir -e .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
