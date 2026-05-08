import json
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import aio_pika
import pytest

from app.services.rabbitmq_producer import (
    PARCELS_QUEUE_NAME,
    RabbitMQProducerService,
)


@pytest.fixture
def test_rabbitmq_producer_dependencies() -> SimpleNamespace:
    """
    Возвращает набор моков для тестирования RabbitMQ producer.
    """
    queue = AsyncMock()
    queue.name = PARCELS_QUEUE_NAME

    default_exchange = AsyncMock()

    channel = AsyncMock()
    channel.declare_queue.return_value = queue
    channel.default_exchange = default_exchange

    connection = AsyncMock()
    connection.channel.return_value = channel

    return SimpleNamespace(
        connection=connection,
        channel=channel,
        queue=queue,
        default_exchange=default_exchange,
    )


@pytest.mark.asyncio
async def test_publish_parcel_created_declares_queue_and_publishes_message(
    test_rabbitmq_producer_dependencies: SimpleNamespace,
) -> None:
    """
    Проверяет, что сервис объявляет очередь и публикует
    сообщение о зарегистрированной посылке.
    """
    parcel_id = uuid4()
    dependencies = test_rabbitmq_producer_dependencies

    service = RabbitMQProducerService(dependencies.connection)

    await service.publish_parcel_created(parcel_id)

    dependencies.connection.channel.assert_awaited_once()
    dependencies.channel.declare_queue.assert_awaited_once_with(
        PARCELS_QUEUE_NAME,
        durable=True,
    )
    dependencies.default_exchange.publish.assert_awaited_once()

    published_message = dependencies.default_exchange.publish.await_args.args[0]
    routing_key = dependencies.default_exchange.publish.await_args.kwargs["routing_key"]

    assert isinstance(published_message, aio_pika.Message)
    assert json.loads(published_message.body.decode("utf-8")) == {
        "parcel_id": str(parcel_id)
    }
    assert routing_key == PARCELS_QUEUE_NAME


@pytest.mark.asyncio
async def test_publish_parcel_created_marks_message_as_persistent(
    test_rabbitmq_producer_dependencies: SimpleNamespace,
) -> None:
    """
    Проверяет, что сервис публикует persistent-сообщение.
    """
    parcel_id = uuid4()
    dependencies = test_rabbitmq_producer_dependencies

    service = RabbitMQProducerService(dependencies.connection)

    await service.publish_parcel_created(parcel_id)

    published_message = dependencies.default_exchange.publish.await_args.args[0]

    assert published_message.delivery_mode == aio_pika.DeliveryMode.PERSISTENT
