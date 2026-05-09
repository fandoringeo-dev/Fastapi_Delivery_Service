# Delivery Service

## ✨ Описание
`Delivery Service` — асинхронный микросервис для международной доставки на `FastAPI`.

Проект позволяет:

- регистрировать посылки без авторизации, но с привязкой к пользовательской cookie-сессии;
- хранить данные о посылках и типах посылок в `PostgreSQL`;
- асинхронно обрабатывать новые посылки через `RabbitMQ` и отдельный worker;
- получать курс `USD/RUB` из внешнего API ЦБ РФ и кешировать его в `Redis`;
- сохранять лог расчётов стоимости доставки в `MongoDB`;
- выгружать логи расчётов из `MongoDB` в `ClickHouse` через `Airflow`;
- смотреть агрегаты по доставке в `Grafana`;
- собирать логи контейнеров в `Loki` через `Promtail`;
- прогонять API под нагрузкой через `Locust`.

## 🥞 Стек технологий

### Backend
- `Python 3.13`
- `FastAPI`
- `SQLAlchemy 2.x`
- `Alembic`
- `Pydantic v2`
- `Loguru`

### Data & Messaging
- `PostgreSQL 17`
- `Redis 8`
- `RabbitMQ 4`
- `MongoDB 8`
- `ClickHouse 25.4`

### Analytics & Observability
- `Apache Airflow 2.10.5`
- `Grafana 11`
- `Loki 3`
- `Promtail 3`

### Testing & Tooling
- `pytest`
- `pytest-asyncio`
- `ruff`
- `Locust`
- `uv`
- `Docker / Docker Compose`

## 🧱 Архитектура

### Основной поток обработки
1. Клиент вызывает `POST /api/v1/parcels/`.
2. API валидирует входные данные и создаёт запись о посылке в `PostgreSQL` со статусом `pending`.
3. API публикует сообщение о новой посылке в очередь `RabbitMQ`.
4. Worker читает сообщение из очереди, получает курс `USD/RUB` через `ExchangeRateService` и кеширует его в `Redis`.
5. Worker рассчитывает стоимость доставки и обновляет посылку в `PostgreSQL`.
6. Worker пишет лог расчёта в `MongoDB`.
7. DAG в `Airflow` забирает лог расчёта из `MongoDB` и загружает его в `ClickHouse`.
8. `Grafana` показывает агрегаты по данным из `ClickHouse`, а `Loki` отображает логи сервисов.

### Формула расчёта доставки

```text
(вес_кг * 0.5 + стоимость_в_долларах * 0.01) * курс_USD_RUB
```

## 🚀 Быстрый старт

### 1. Поднять весь стек

```bash
docker compose up -d --build
```

### 2. Накатить аналитические view для ClickHouse

`init_clickhouse.sql` создаёт таблицу автоматически, а представления для Grafana создаются отдельной командой:

```powershell
Get-Content .\analytics\sql\views.sql | docker compose exec -T clickhouse clickhouse-client --multiquery
```

### 3. Проверить доступность сервисов

- API: `http://localhost:8000`
- Swagger UI: `http://localhost:8000/docs`
- RabbitMQ Management: `http://localhost:15672`
- Airflow: `http://localhost:8080`
- Grafana: `http://localhost:3000`
- ClickHouse HTTP: `http://localhost:8123`
- Loki: `http://localhost:3100`

### 4. Учётные данные UI

- Airflow:
  - login: `admin`
  - password: `admin`
- Grafana:
  - login: `admin`
  - password: `admin`
- RabbitMQ:
  - login: `guest`
  - password: `guest`

## ⚙️ Переменные окружения

Проект использует три env-файла:

- `.env` — основной docker-контур;
- `.env.local` — локальный запуск из хоста;
- `.env.test` — тестовый контур.

### Основные переменные приложения

| Переменная | Назначение |
|---|---|
| `APP_NAME` | Имя приложения в FastAPI |
| `DEBUG` | Режим отладки |
| `API_V1_PREFIX` | Префикс API, по умолчанию `/api/v1` |

### PostgreSQL

| Переменная | Назначение |
|---|---|
| `POSTGRES_HOST` | Хост PostgreSQL |
| `POSTGRES_PORT` | Порт PostgreSQL |
| `POSTGRES_DB` | Имя базы |
| `POSTGRES_USER` | Пользователь |
| `POSTGRES_PASSWORD` | Пароль |

### Redis

| Переменная | Назначение |
|---|---|
| `REDIS_HOST` | Хост Redis |
| `REDIS_PORT` | Порт Redis |

### RabbitMQ

| Переменная | Назначение |
|---|---|
| `RABBITMQ_HOST` | Хост RabbitMQ |
| `RABBITMQ_PORT` | Порт RabbitMQ |
| `RABBITMQ_USER` | Пользователь RabbitMQ |
| `RABBITMQ_PASSWORD` | Пароль RabbitMQ |

### MongoDB

| Переменная | Назначение |
|---|---|
| `MONGODB_HOST` | Хост MongoDB |
| `MONGODB_PORT` | Порт MongoDB |
| `MONGODB_DB` | Имя базы MongoDB |

### ClickHouse

| Переменная | Назначение |
|---|---|
| `CLICKHOUSE_HOST` | Хост ClickHouse |
| `CLICKHOUSE_PORT` | HTTP-порт ClickHouse |
| `CLICKHOUSE_DB` | Аналитическая база |
| `CLICKHOUSE_USER` | Пользователь ClickHouse |
| `CLICKHOUSE_PASSWORD` | Пароль ClickHouse |

### Airflow

| Переменная | Назначение |
|---|---|
| `AIRFLOW_POSTGRES_DB` | Служебная БД Airflow |
| `AIRFLOW_POSTGRES_USER` | Пользователь metadata DB |
| `AIRFLOW_POSTGRES_PASSWORD` | Пароль metadata DB |
| `AIRFLOW_FERNET_KEY` | Ключ шифрования Airflow |
| `AIRFLOW_ADMIN_USERNAME` | Логин администратора Airflow |
| `AIRFLOW_ADMIN_PASSWORD` | Пароль администратора Airflow |
| `AIRFLOW_ADMIN_EMAIL` | Email администратора Airflow |

## 🔧 Установка

### Вариант 1. Рекомендуемый: через Docker Compose

```bash
docker compose up -d --build
```

После старта:

1. дождаться, пока поднимутся `app`, `worker`, `postgres`, `redis`, `rabbitmq`, `mongodb`;
2. дождаться инициализации `clickhouse-init` и `airflow-init`;
3. применить `views.sql` в `ClickHouse`;
4. открыть `Swagger`, `Airflow` и `Grafana`.

### Вариант 2. Локальная установка через `uv`

```bash
uv sync
```

Для локального запуска нужен уже поднятый инфраструктурный контур либо доступные извне зависимости:

```bash
uv run alembic upgrade head
uv run uvicorn app.main:app --app-dir src --reload
```

Worker запускается отдельно:

```bash
uv run python -m app.workers.run_parcel_worker
```

## 🗄️ Базы и данные

### PostgreSQL
Хранит:

- типы посылок;
- сами посылки;
- статус обработки;
- рассчитанную стоимость доставки;
- привязку транспортной компании.

Сидируются типы посылок:

- `1` — `Одежда`
- `2` — `Электроника`
- `3` — `Разное`

### Redis
Используется для кеширования курса `USD/RUB` на 12 часов.

### RabbitMQ
Используется как транспорт для асинхронной обработки новых посылок.

### MongoDB
Хранит лог расчёта стоимости доставки в коллекции `delivery_cost_calculation_logs`.

### ClickHouse
Используется как аналитическое хранилище.

Таблица:

- `delivery_analytics.delivery_cost_calculations`

Представления:

- `delivery_analytics.delivery_cost_total_view`
- `delivery_analytics.delivery_cost_max_view`
- `delivery_analytics.delivery_cost_min_view`

## 📊 Аналитика

### Airflow

В проекте настроен DAG:

- `mongodb_to_clickhouse_delivery_costs`

Он:

- читает логи расчётов из `MongoDB`;
- загружает их в `ClickHouse`;
- пропускает дубли по паре `parcel_id + calculated_at`.

### Grafana

Provisioning в проекте автоматически поднимает:

- datasource `clickhouse`;
- datasource `loki`;
- dashboard `Delivery Analytics`.

Dashboard `Delivery Analytics` показывает:

- сумму стоимостей доставок;
- максимальную стоимость доставки;
- минимальную стоимость доставки.

## 🪵 Логирование и мониторинг

### Loki + Promtail

`Promtail` собирает логи контейнеров Docker и отправляет их в `Loki`.

Datasource `loki` подключается к `Grafana` автоматически через provisioning.

### Grafana

Используется для:

- просмотра логов в `Explore -> loki`;
- просмотра аналитических показателей из `ClickHouse`.

## 🧪 Тесты

В проекте есть:

- API-тесты;
- repository-тесты;
- service-тесты;
- тесты логирования расчётов;
- тесты producer-сервиса RabbitMQ.

Всего в проекте сейчас `64` теста.

### Рекомендуемый запуск тестов в docker-контуре

```bash
docker compose -f docker-compose.test.yml up --build tests
```

### Локальный запуск тестов

```bash
uv run pytest
```

### Линтер и форматирование

```bash
make lint
make fmt
make test
make check
```

## 🔌 API

### Документация

- Swagger UI: `http://localhost:8000/docs`

### Основные роуты

| Метод | Роут | Назначение |
|---|---|---|
| `GET` | `/api/v1/health` | Проверка доступности сервиса |
| `GET` | `/api/v1/parcel-types` | Получить список типов посылок |
| `POST` | `/api/v1/parcels/` | Зарегистрировать посылку |
| `GET` | `/api/v1/parcels/` | Получить свои посылки с пагинацией и фильтрами |
| `GET` | `/api/v1/parcels/{parcel_id}` | Получить посылку по `id` |
| `POST` | `/api/v1/parcels/{parcel_id}/assign-company` | Привязать транспортную компанию |

### Пример регистрации посылки

```http
POST /api/v1/parcels/
Content-Type: application/json
```

```json
{
  "name": "Телефон",
  "weight_kg": "1.500",
  "type_id": 2,
  "declared_value_usd": "1000.00"
}
```

Пример ответа:

```json
{
  "id": "2f9936d6-0c9c-40cb-b7f1-1d4ce0fd6248",
  "status": "pending"
}
```

### Пагинация и фильтры списка посылок

Поддерживаются параметры:

- `page`
- `page_size`
- `type_id`
- `has_delivery_cost`

Пример:

```http
GET /api/v1/parcels/?page=1&page_size=10&type_id=2&has_delivery_cost=true
```

## 🧪 Нагрузочное тестирование

Минимальный сценарий для `Locust` находится в:

- `load_tests/locustfile.py`

Сценарий:

- создаёт посылки;
- читает список посылок;
- читает отдельную посылку по `id`.

### Запуск

```bash
uv run locust -f load_tests/locustfile.py
```

UI Locust:

- `http://localhost:8089`

Стартовый прогон:

- `Number of users`: `10`
- `Ramp up`: `2`
- `Host`: `http://localhost:8000`

Более тяжёлый локальный прогон:

- `Number of users`: `50`
- `Ramp up`: `5`
- `Run time`: `5m`

## 📁 Структура проекта

```text
src/                     основной backend-код
analytics/               DAG, ClickHouse SQL и аналитический конфиг
monitoring/              Loki и provisioning Grafana
load_tests/              сценарии нагрузочного тестирования
tests/                   API, repository и service тесты
docker/                  Dockerfile и entrypoint-скрипты
migrations/              миграции Alembic
```

## 📝 Что важно знать

- Авторизации в проекте нет, доступ к посылкам ограничен cookie-сессией.
- Регистрация посылки идёт через API, а расчёт стоимости выполняется асинхронно worker'ом.
- Для аналитики в `Grafana` после первого старта нужно один раз применить `analytics/sql/views.sql`, так как `docker-compose` автоматически создаёт таблицу, но не создаёт `VIEW`.
- `Airflow` уже настроен для ручного и планового запуска DAG из UI.
- `Grafana` datasource и dashboard подхватываются автоматически из provisioning-файлов проекта.
