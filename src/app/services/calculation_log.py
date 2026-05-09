from datetime import UTC, datetime
from decimal import Decimal

from pymongo.asynchronous.database import AsyncDatabase

from app.models.parcel import Parcel


class CalculationLogService:
    """
    Сервис для записи логов расчета стоимости доставки в MongoDB.
    """

    def __init__(self, database: AsyncDatabase) -> None:
        """
        Инициализирует сервис.

        :param database: Асинхронная база данных MongoDB.
        """
        self.database = database
        self.collection = database["delivery_cost_calculation_logs"]

    async def create_log(
        self,
        parcel: Parcel,
        usd_to_rub_rate: Decimal,
    ) -> None:
        """
        Сохраняет лог расчета стоимости доставки в MongoDB.

        """
        await self.collection.insert_one(
            {
                "parcel_id": str(parcel.id),
                "parcel_type_id": parcel.parcel_type.id,
                "parcel_type_name": parcel.parcel_type.name,
                "weight_kg": str(parcel.weight_kg),
                "declared_value_usd": str(parcel.declared_value_usd),
                "usd_to_rub_rate": str(usd_to_rub_rate),
                "delivery_cost_rub": str(parcel.delivery_cost_rub),
                "calculated_at": datetime.now(UTC),
            }
        )
