from decimal import Decimal

import httpx
from loguru import logger
from redis.asyncio import Redis

CBR_DAILY_JSON_URL = "https://www.cbr-xml-daily.ru/daily_json.js"
USD_RATE_CACHE_KEY = "usd_rub_rate"
USD_RATE_CACHE_TTL_SECONDS = 60 * 60 * 12


class ExchangeRateService:
    """
    Сервис для получения курса доллара к рублю.
    """

    def __init__(self, redis_client: Redis) -> None:
        """
        Инициализирует сервис.

        :param redis_client: Асинхронный Redis-клиент.
        """
        self.redis_client = redis_client

    async def get_usd_to_rub_rate(self) -> Decimal:
        """
        Возвращает курс доллара к рублю с использованием кеша Redis.

        :return: Курс доллара к рублю.
        """
        cached_rate = await self.redis_client.get(USD_RATE_CACHE_KEY)
        if cached_rate is not None:
            logger.info("Курс USD/RUB получен из кеша Redis.")
            return Decimal(cached_rate)

        logger.info(
            "Курс USD/RUB отсутствует в кеше. Выполняется запрос во внешний API."
        )

        async with httpx.AsyncClient() as client:
            response = await client.get(CBR_DAILY_JSON_URL)
            response.raise_for_status()
            data = response.json()

        usd_rate = Decimal(str(data["Valute"]["USD"]["Value"]))

        await self.redis_client.set(
            USD_RATE_CACHE_KEY,
            str(usd_rate),
            ex=USD_RATE_CACHE_TTL_SECONDS,
        )

        logger.info("Курс USD/RUB получен из внешнего API и сохранен в Redis.")

        return usd_rate
