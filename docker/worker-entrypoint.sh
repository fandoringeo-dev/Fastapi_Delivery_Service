#!/bin/sh
# Скрипт инициализации контейнера worker:
# ожидает готовности PostgreSQL, затем запускает worker обработки посылок.
set -e

echo "Waiting for PostgreSQL..."

until uv run python -c "import psycopg; psycopg.connect('postgresql://$POSTGRES_USER:$POSTGRES_PASSWORD@$POSTGRES_HOST:$POSTGRES_PORT/$POSTGRES_DB').close()"; do
  echo "PostgreSQL is unavailable - retrying..."
  sleep 2
done

export PYTHONPATH=/app/src

echo "Starting parcel worker..."
exec uv run python -m app.workers.run_parcel_worker
