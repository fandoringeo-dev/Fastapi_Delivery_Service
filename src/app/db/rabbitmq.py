import aio_pika

from app.core.config import settings


async def get_rabbitmq_connection() -> aio_pika.abc.AbstractRobustConnection:
    """
    Возвращает устойчивое подключение к RabbitMQ.

    :return: Подключение к RabbitMQ.
    """
    return await aio_pika.connect_robust(settings.rabbitmq_url)
