import os

os.environ["ENV_FILE"] = ".env.test"

from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from pymongo import AsyncMongoClient
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.db.base import Base
from app.db.dependencies import get_db_session
from app.main import app
from app.models.parcel import Parcel
from app.models.parcel_type import ParcelType
from tests.config import test_settings

TEST_PARCEL_TYPES = (
    {"id": 1, "name": "Одежда"},
    {"id": 2, "name": "Электроника"},
    {"id": 3, "name": "Разное"},
)


class DummyRabbitMQConnection:
    """
    Заглушка подключения к RabbitMQ для API-тестов.
    """

    pass


@pytest_asyncio.fixture(scope="session", loop_scope="session")
async def test_engine() -> AsyncGenerator:
    engine = create_async_engine(
        test_settings.postgres_url_test,
        echo=False,
        poolclass=NullPool,
    )

    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)
        await connection.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture
async def test_session_factory(test_engine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(
        bind=test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )


@pytest_asyncio.fixture
async def test_db_session(
    test_session_factory: async_sessionmaker[AsyncSession],
) -> AsyncGenerator[AsyncSession]:
    async with test_session_factory() as session:
        await session.execute(delete(Parcel))
        await session.execute(delete(ParcelType))

        session.add_all(
            [ParcelType(id=item["id"], name=item["name"]) for item in TEST_PARCEL_TYPES]
        )
        await session.commit()

        yield session


@pytest_asyncio.fixture
async def test_client(
    test_db_session: AsyncSession,
    test_session_factory: async_sessionmaker[AsyncSession],
    monkeypatch: pytest.MonkeyPatch,
) -> AsyncGenerator[AsyncClient]:
    async def override_get_db_session() -> AsyncGenerator[AsyncSession]:
        async with test_session_factory() as session:
            yield session

    async def fake_get_rabbitmq_connection() -> DummyRabbitMQConnection:
        return DummyRabbitMQConnection()

    async def fake_publish_parcel_created(self, parcel_id) -> None:
        return None

    app.dependency_overrides[get_db_session] = override_get_db_session

    monkeypatch.setattr(
        "app.api.v1.routers.parcel.get_rabbitmq_connection",
        fake_get_rabbitmq_connection,
    )
    monkeypatch.setattr(
        "app.services.rabbitmq_producer.RabbitMQProducerService.publish_parcel_created",
        fake_publish_parcel_created,
    )

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as async_client:
        yield async_client

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def test_mongodb_database() -> AsyncGenerator:
    """
    Возвращает тестовую базу данных MongoDB и очищает коллекцию логов расчета.
    """
    client = AsyncMongoClient(test_settings.mongodb_url_test)
    database = client[test_settings.mongodb_db_test]

    await database["delivery_cost_calculation_logs"].delete_many({})

    yield database

    await database["delivery_cost_calculation_logs"].delete_many({})
    await client.close()
