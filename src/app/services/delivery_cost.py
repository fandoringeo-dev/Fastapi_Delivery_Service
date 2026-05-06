from decimal import ROUND_HALF_UP, Decimal


class DeliveryCostService:
    """
    Сервис для расчета стоимости доставки.
    """

    async def calculate_delivery_cost(
        self,
        weight_kg: Decimal,
        declared_value_usd: Decimal,
        usd_to_rub_rate: Decimal,
    ) -> Decimal:
        """
        Рассчитывает стоимость доставки в рублях.

        :param weight_kg: Вес посылки в килограммах.
        :param declared_value_usd: Стоимость содержимого в долларах.
        :param usd_to_rub_rate: Курс доллара к рублю.
        :return: Стоимость доставки в рублях.
        """
        delivery_cost = (
            weight_kg * Decimal("0.5") + declared_value_usd * Decimal("0.01")
        ) * usd_to_rub_rate

        return delivery_cost.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
