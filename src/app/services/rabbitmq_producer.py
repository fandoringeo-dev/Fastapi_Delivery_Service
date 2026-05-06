import json
from uuid import UUID

import aio_pika
from loguru import logger

PARCELS_QUEUE_NAME = "parcels"


class RabbitMQProducerService:
    """
    Сервис публикации сообщений в RabbitMQ.
    """

    def __init__(self, connection: aio_pika.abc.AbstractRobustConnection) -> None:
        """
        Инициализирует сервис.

        :param connection: Подключение к RabbitMQ.
        """
        self.connection = connection

    async def publish_parcel_created(self, parcel_id: UUID) -> None:
        """
        Публикует сообщение о зарегистрированной посылке.

        :param parcel_id: Идентификатор посылки.
        """
        channel = await self.connection.channel()
        queue = await channel.declare_queue(PARCELS_QUEUE_NAME, durable=True)

        message_body = json.dumps({"parcel_id": str(parcel_id)}).encode("utf-8")

        await channel.default_exchange.publish(
            aio_pika.Message(
                body=message_body,
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
            ),
            routing_key=queue.name,
        )

        logger.info(
            "Сообщение о посылке отправлено в RabbitMQ: parcel_id={}", parcel_id
        )
