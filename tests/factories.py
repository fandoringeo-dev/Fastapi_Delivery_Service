from datetime import datetime
from decimal import Decimal
from unittest.mock import AsyncMock
from uuid import uuid4

from httpx import AsyncClient

from app.common.enums import ParcelStatus
from app.models.parcel import Parcel
from app.schemas.parcel import ParcelCreateRequest


def build_test_parcel(**overrides) -> Parcel:
    """
    Создает тестовую посылку с возможностью переопределения полей.
    """
    parcel = Parcel(
        id=uuid4(),
        client_session_id="session-1",
        name="Телефон",
        status=ParcelStatus.PENDING,
        weight_kg=Decimal("1.500"),
        type_id=2,
        declared_value_usd=Decimal("1000.00"),
        delivery_cost_rub=None,
        company_id=None,
        created_at=datetime.now(),
    )

    for field_name, value in overrides.items():
        setattr(parcel, field_name, value)

    return parcel


def build_test_repository() -> AsyncMock:
    """
    Создает тестовый мок репозитория посылок.
    """
    repository = AsyncMock()
    repository.session = AsyncMock()
    return repository


def build_test_parcel_create_request(**overrides) -> ParcelCreateRequest:
    """
    Создает тестовый запрос на регистрацию посылки.
    """
    payload = {
        "name": "Телефон",
        "weight_kg": Decimal("1.500"),
        "type_id": 2,
        "declared_value_usd": Decimal("1000.00"),
    }
    payload.update(overrides)
    return ParcelCreateRequest(**payload)


def build_create_parcel_payload(**overrides) -> dict:
    """
    Создает тестовый payload для регистрации посылки.
    """
    payload = {
        "name": "Телефон",
        "weight_kg": "1.500",
        "type_id": 2,
        "declared_value_usd": "1000.00",
    }
    payload.update(overrides)
    return payload


async def create_parcel(
    test_client: AsyncClient,
    *,
    name: str = "Телефон",
    weight_kg: str = "1.500",
    type_id: int = 2,
    declared_value_usd: str = "1000.00",
) -> dict:
    """
    Создает посылку через API и возвращает тело ответа.
    """
    response = await test_client.post(
        "/api/v1/parcels/",
        json=build_create_parcel_payload(
            name=name,
            weight_kg=weight_kg,
            type_id=type_id,
            declared_value_usd=declared_value_usd,
        ),
    )

    assert response.status_code == 201
    return response.json()
