from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.services.exchange_rate import (
    CBR_DAILY_JSON_URL,
    USD_RATE_CACHE_KEY,
    ExchangeRateService,
)


@pytest.mark.asyncio
async def test_get_usd_to_rub_rate_returns_cached_value_from_redis() -> None:
    """
    Проверяет, что сервис возвращает курс из Redis, если он уже закеширован.
    """
    redis_client = AsyncMock()
    redis_client.get.return_value = "81.55"

    service = ExchangeRateService(redis_client)

    result = await service.get_usd_to_rub_rate()

    assert result == Decimal("81.55")
    redis_client.get.assert_awaited_once_with(USD_RATE_CACHE_KEY)
    redis_client.set.assert_not_called()


@pytest.mark.asyncio
async def test_get_usd_to_rub_rate_requests_external_api_when_cache_is_empty(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    Проверяет, что сервис запрашивает курс из внешнего API, если кеш Redis пустой.
    """
    redis_client = AsyncMock()
    redis_client.get.return_value = None

    response = MagicMock()
    response.json.return_value = {
        "Valute": {
            "USD": {
                "Value": 79.45,
            }
        }
    }
    response.raise_for_status.return_value = None

    client = AsyncMock()
    client.get.return_value = response

    async_context_manager = AsyncMock()
    async_context_manager.__aenter__.return_value = client
    async_context_manager.__aexit__.return_value = None

    monkeypatch.setattr(
        "app.services.exchange_rate.httpx.AsyncClient",
        lambda: async_context_manager,
    )

    service = ExchangeRateService(redis_client)

    result = await service.get_usd_to_rub_rate()

    assert result == Decimal("79.45")
    redis_client.get.assert_awaited_once_with(USD_RATE_CACHE_KEY)
    client.get.assert_awaited_once_with(CBR_DAILY_JSON_URL)
    redis_client.set.assert_awaited_once()
