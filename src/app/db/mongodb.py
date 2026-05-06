from pymongo import AsyncMongoClient
from pymongo.asynchronous.database import AsyncDatabase

from app.core.config import settings


def get_mongodb_database() -> AsyncDatabase:
    """
    Возвращает объект базы данных MongoDB.

    :return: Асинхронная база данных MongoDB.
    """
    client = AsyncMongoClient(settings.mongodb_url)
    return client[settings.mongodb_db]
