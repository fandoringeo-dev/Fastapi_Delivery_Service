from unittest.mock import AsyncMock

import pytest

from app.models.parcel_type import ParcelType
from app.services.parcel_type import ParcelTypeService


@pytest.mark.asyncio
async def test_get_all_returns_parcel_types_from_repository() -> None:
    """
    Проверяет, что сервис возвращает список типов посылок из репозитория.
    """
    parcel_types = [
        ParcelType(id=1, name="Одежда"),
        ParcelType(id=2, name="Электроника"),
        ParcelType(id=3, name="Разное"),
    ]

    repository = AsyncMock()
    repository.get_all.return_value = parcel_types

    service = ParcelTypeService(repository)

    result = await service.get_all()

    assert result == parcel_types
    repository.get_all.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_all_returns_empty_list_when_repository_returns_empty_list() -> None:
    """
    Проверяет, что сервис возвращает пустой список,
    если репозиторий не вернул типов посылок.
    """
    repository = AsyncMock()
    repository.get_all.return_value = []

    service = ParcelTypeService(repository)

    result = await service.get_all()

    assert result == []
    repository.get_all.assert_awaited_once()
