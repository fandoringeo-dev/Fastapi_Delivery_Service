import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_get_parcel_types_returns_status_code_200(
    test_client: AsyncClient,
) -> None:
    """
    Проверяет, что endpoint получения типов посылок возвращает статус-код 200.
    """
    response = await test_client.get("/api/v1/parcel-types")

    assert response.status_code == 200


@pytest.mark.asyncio
async def test_get_parcel_types_returns_seeded_parcel_types(
    test_client: AsyncClient,
) -> None:
    """
    Проверяет, что endpoint возвращает предзаполненные типы посылок.
    """
    response = await test_client.get("/api/v1/parcel-types")

    assert response.json() == [
        {"id": 1, "name": "Одежда"},
        {"id": 2, "name": "Электроника"},
        {"id": 3, "name": "Разное"},
    ]


@pytest.mark.asyncio
async def test_get_parcel_types_returns_response_in_expected_format(
    test_client: AsyncClient,
) -> None:
    """
    Проверяет, что endpoint возвращает список объектов с полями id и name.
    """
    response = await test_client.get("/api/v1/parcel-types")

    data = response.json()

    assert isinstance(data, list)
    assert len(data) == 3

    for item in data:
        assert set(item.keys()) == {"id", "name"}
        assert isinstance(item["id"], int)
        assert isinstance(item["name"], str)
