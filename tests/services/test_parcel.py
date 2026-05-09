from datetime import datetime
from decimal import Decimal
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.models.parcel_type import ParcelType
from app.schemas.parcel import ParcelListQueryParams
from app.services.parcel import ParcelService
from tests.factories import (
    build_test_parcel,
    build_test_parcel_create_request,
    build_test_repository,
)


@pytest.mark.asyncio
async def test_create_parcel_creates_parcel_when_type_exists() -> None:
    """
    Проверяет, что сервис создает посылку, если указанный тип существует.
    """
    repository = build_test_repository()

    created_parcel = build_test_parcel()
    repository.create.return_value = created_parcel

    producer = AsyncMock()

    service = ParcelService(repository, producer)
    service.parcel_type_repository = AsyncMock()
    service.parcel_type_repository.get_parcel_type.return_value = ParcelType(
        id=2,
        name="Электроника",
    )

    parcel_data = build_test_parcel_create_request()

    result = await service.create_parcel(parcel_data, "session-1")

    assert result == created_parcel
    repository.create.assert_awaited_once()
    repository.session.commit.assert_awaited_once()
    producer.publish_parcel_created.assert_awaited_once_with(created_parcel.id)


@pytest.mark.asyncio
async def test_create_parcel_raises_400_when_type_does_not_exist() -> None:
    """
    Проверяет, что сервис возвращает ошибку 400, если тип посылки не существует.
    """
    repository = build_test_repository()

    producer = AsyncMock()

    service = ParcelService(repository, producer)
    service.parcel_type_repository = AsyncMock()
    service.parcel_type_repository.get_parcel_type.return_value = None

    parcel_data = build_test_parcel_create_request(type_id=999)

    with pytest.raises(HTTPException) as exc_info:
        await service.create_parcel(parcel_data, "session-1")

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "Указанный тип посылки не существует"
    repository.create.assert_not_called()


@pytest.mark.asyncio
async def test_read_parcel_by_id_returns_parcel_for_owner_session() -> None:
    """
    Проверяет, что сервис возвращает посылку, принадлежащую текущей сессии.
    """
    parcel = build_test_parcel()

    repository = build_test_repository()
    repository.get_parcel_by_id.return_value = parcel

    service = ParcelService(repository)

    result = await service.read_parcel_by_id(parcel.id, "session-1")

    assert result == parcel
    repository.get_parcel_by_id.assert_awaited_once_with(parcel_id=parcel.id)


@pytest.mark.asyncio
async def test_read_parcel_by_id_raises_400_when_session_is_missing() -> None:
    """
    Проверяет, что сервис возвращает ошибку 400 при отсутствии идентификатора сессии.
    """
    repository = build_test_repository()

    service = ParcelService(repository)

    with pytest.raises(HTTPException) as exc_info:
        await service.read_parcel_by_id(uuid4(), None)

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "Отсутствует идентификатор сессии."


@pytest.mark.asyncio
async def test_read_parcel_by_id_raises_404_when_parcel_does_not_exist() -> None:
    """
    Проверяет, что сервис возвращает ошибку 404, если посылка не существует.
    """
    repository = build_test_repository()
    repository.get_parcel_by_id.return_value = None

    service = ParcelService(repository)

    with pytest.raises(HTTPException) as exc_info:
        await service.read_parcel_by_id(uuid4(), "session-1")

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Посылка с указанным id не существует"


@pytest.mark.asyncio
async def test_read_parcel_by_id_raises_403_for_foreign_parcel() -> None:
    """
    Проверяет, что сервис возвращает ошибку 403 при попытке получить чужую посылку.
    """
    parcel = build_test_parcel()

    repository = build_test_repository()
    repository.get_parcel_by_id.return_value = parcel

    service = ParcelService(repository)

    with pytest.raises(HTTPException) as exc_info:
        await service.read_parcel_by_id(parcel.id, "foreign-session")

    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == "Посылка с указанным id не принадлежит пользователю"


@pytest.mark.asyncio
async def test_get_parcels_returns_paginated_response() -> None:
    """
    Проверяет, что сервис возвращает список посылок с пагинацией.
    """
    parcels = [
        build_test_parcel(
            parcel_type=ParcelType(id=1, name="Одежда"),
            created_at=datetime.now(),
        ),
        build_test_parcel(
            name="Куртка",
            weight_kg=Decimal("2.000"),
            type_id=1,
            declared_value_usd=Decimal("300.00"),
            parcel_type=ParcelType(id=1, name="Одежда"),
            created_at=datetime.now(),
        ),
    ]

    repository = build_test_repository()
    repository.get_all_by_session_id.return_value = parcels
    repository.count_by_session_id.return_value = 2

    service = ParcelService(repository)

    query_params = ParcelListQueryParams(page=1, page_size=10)

    result = await service.get_parcels("session-1", query_params)

    assert len(result.items) == 2
    assert result.items[0].name == "Телефон"
    assert result.items[1].name == "Куртка"
    assert result.total == 2
    assert result.page == 1
    assert result.page_size == 10


@pytest.mark.asyncio
async def test_get_parcels_raises_400_when_session_is_missing() -> None:
    """
    Проверяет, что сервис возвращает ошибку 400 при отсутствии идентификатора сессии.
    """
    repository = build_test_repository()

    service = ParcelService(repository)

    query_params = ParcelListQueryParams(page=1, page_size=10)

    with pytest.raises(HTTPException) as exc_info:
        await service.get_parcels(None, query_params)

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "Отсутствует идентификатор сессии."


@pytest.mark.asyncio
async def test_assign_company_to_parcel_completes_successfully_for_free_parcel() -> (
    None
):
    """
    Проверяет, что сервис успешно привязывает компанию к свободной посылке.
    """
    parcel = build_test_parcel()

    repository = build_test_repository()
    repository.get_parcel_by_id.return_value = parcel
    repository.assign_company_if_unassigned.return_value = 1

    service = ParcelService(repository)

    await service.assign_company_to_parcel(parcel.id, 10)

    repository.assign_company_if_unassigned.assert_awaited_once_with(
        parcel_id=parcel.id,
        company_id=10,
    )


@pytest.mark.asyncio
async def test_assign_company_to_parcel_raises_404_for_nonexistent_parcel() -> None:
    """
    Проверяет, что сервис возвращает ошибку 404, если посылка не существует.
    """
    repository = build_test_repository()
    repository.get_parcel_by_id.return_value = None

    service = ParcelService(repository)

    with pytest.raises(HTTPException) as exc_info:
        await service.assign_company_to_parcel(uuid4(), 10)

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Посылка с указанным id не существует"


@pytest.mark.asyncio
async def test_assign_company_to_parcel_raises_409_for_taken_parcel() -> None:
    """
    Проверяет, что сервис возвращает ошибку 409, если посылка уже занята.
    """
    parcel = build_test_parcel(
        company_id=10,
    )

    repository = build_test_repository()
    repository.get_parcel_by_id.return_value = parcel
    repository.assign_company_if_unassigned.return_value = 0

    service = ParcelService(repository)

    with pytest.raises(HTTPException) as exc_info:
        await service.assign_company_to_parcel(parcel.id, 20)

    assert exc_info.value.status_code == 409
    assert exc_info.value.detail == "Посылка уже привязана к транспортной компании"
