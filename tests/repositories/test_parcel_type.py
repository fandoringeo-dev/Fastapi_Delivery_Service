import pytest

from app.repositories.parcel_type import ParcelTypeRepository


@pytest.mark.asyncio
async def test_get_all_returns_all_seeded_parcel_types(
    test_db_session,
) -> None:
    """
    Проверяет, что репозиторий возвращает все предзаполненные типы посылок.
    """
    repository = ParcelTypeRepository(test_db_session)

    parcel_types = await repository.get_all()

    assert len(parcel_types) == 3
    assert [parcel_type.id for parcel_type in parcel_types] == [1, 2, 3]
    assert [parcel_type.name for parcel_type in parcel_types] == [
        "Одежда",
        "Электроника",
        "Разное",
    ]


@pytest.mark.asyncio
async def test_get_parcel_type_returns_parcel_type_by_id(
    test_db_session,
) -> None:
    """
    Проверяет, что репозиторий возвращает тип посылки по его идентификатору.
    """
    repository = ParcelTypeRepository(test_db_session)

    parcel_type = await repository.get_parcel_type(2)

    assert parcel_type is not None
    assert parcel_type.id == 2
    assert parcel_type.name == "Электроника"


@pytest.mark.asyncio
async def test_get_parcel_type_returns_none_for_nonexistent_id(
    test_db_session,
) -> None:
    """
    Проверяет, что репозиторий возвращает None для несуществующего типа посылки.
    """
    repository = ParcelTypeRepository(test_db_session)

    parcel_type = await repository.get_parcel_type(999)

    assert parcel_type is None
