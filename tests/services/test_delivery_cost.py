from decimal import Decimal

import pytest

from app.services.delivery_cost import DeliveryCostService


@pytest.mark.asyncio
async def test_calculate_delivery_cost_returns_expected_value() -> None:
    """
    Проверяет, что сервис корректно рассчитывает стоимость доставки.
    """
    service = DeliveryCostService()

    result = await service.calculate_delivery_cost(
        weight_kg=Decimal("10.000"),
        declared_value_usd=Decimal("100.00"),
        usd_to_rub_rate=Decimal("80.00"),
    )

    assert result == Decimal("480.00")


@pytest.mark.asyncio
async def test_calculate_delivery_cost_rounds_result_to_two_decimal_places() -> None:
    """
    Проверяет, что сервис округляет стоимость доставки до двух знаков после запятой.
    """
    service = DeliveryCostService()

    result = await service.calculate_delivery_cost(
        weight_kg=Decimal("1.333"),
        declared_value_usd=Decimal("10.00"),
        usd_to_rub_rate=Decimal("91.27"),
    )

    assert result == Decimal("69.96")
