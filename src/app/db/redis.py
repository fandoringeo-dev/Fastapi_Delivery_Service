import redis.asyncio as redis

from app.core.config import settings


def get_redis_client() -> redis.Redis:
    """
    Возвращает Redis-клиент.

    :return: Асинхронный Redis-клиент.
    """
    return redis.from_url(
        settings.redis_url,
        encoding="utf-8",
        decode_responses=True,
    )
