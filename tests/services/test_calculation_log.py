from decimal import Decimal
from uuid import uuid4

import pytest

from app.common.enums import ParcelStatus
from app.models.parcel import Parcel
from app.models.parcel_type import ParcelType
from app.services.calculation_log import CalculationLogService


@pytest.mark.asyncio
async def test_create_log_saves_document_to_mongodb_collection(
    test_mongodb_database,
) -> None:
    """
    Проверяет, что сервис сохраняет лог расчета стоимости доставки в MongoDB.
    """
    service = CalculationLogService(test_mongodb_database)

    parcel = Parcel(
        id=uuid4(),
        client_session_id="session-1",
        name="Телефон",
        status=ParcelStatus.PROCESSED,
        weight_kg=Decimal("1.500"),
        type_id=2,
        declared_value_usd=Decimal("1000.00"),
        delivery_cost_rub=Decimal("1500.50"),
        company_id=None,
    )
    parcel.parcel_type = ParcelType(id=2, name="Электроника")

    usd_to_rub_rate = Decimal("79.45")

    await service.create_log(parcel=parcel, usd_to_rub_rate=usd_to_rub_rate)

    saved_document = await test_mongodb_database[
        "delivery_cost_calculation_logs"
    ].find_one({"parcel_id": str(parcel.id)})

    assert saved_document is not None
    assert saved_document["parcel_id"] == str(parcel.id)
    assert saved_document["parcel_type_id"] == 2
    assert saved_document["parcel_type_name"] == "Электроника"
    assert saved_document["weight_kg"] == "1.500"
    assert saved_document["declared_value_usd"] == "1000.00"
    assert saved_document["usd_to_rub_rate"] == "79.45"
    assert saved_document["delivery_cost_rub"] == "1500.50"
    assert "calculated_at" in saved_document
