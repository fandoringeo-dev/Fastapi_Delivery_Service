#!/bin/sh
# Скрипт инициализации контейнера приложения:
# ожидает готовности PostgreSQL, применяет стартовые миграции и запускает FastAPI.
set -e


echo "Waiting for PostgreSQL..."

until uv run python -c "import psycopg; psycopg.connect('postgresql://$POSTGRES_USER:$POSTGRES_PASSWORD@$POSTGRES_HOST:$POSTGRES_PORT/$POSTGRES_DB').close()"; do
  echo "PostgreSQL is unavailable - retrying..."
  sleep 2
done

export PYTHONPATH=/app/src

echo "Applying migrations..."

uv run alembic upgrade head

echo "Starting application..."
exec uv run uvicorn app.main:app --app-dir src --host 0.0.0.0 --port 8000 --reload
