from decimal import Decimal
from uuid import uuid4

import pytest

from app.common.enums import ParcelStatus
from app.repositories.parcel import ParcelRepository
from tests.factories import build_test_parcel


@pytest.mark.asyncio
async def test_create_saves_parcel_to_database(
    test_db_session,
) -> None:
    """
    Проверяет, что репозиторий сохраняет посылку в базе данных.
    """
    repository = ParcelRepository(test_db_session)
    parcel = build_test_parcel()

    created_parcel = await repository.create(parcel)
    await test_db_session.commit()

    assert created_parcel.id is not None
    assert created_parcel.name == "Телефон"
    assert created_parcel.client_session_id == "session-1"
    assert created_parcel.status == ParcelStatus.PENDING


@pytest.mark.asyncio
async def test_get_parcel_by_id_returns_saved_parcel(
    test_db_session,
) -> None:
    """
    Проверяет, что репозиторий возвращает сохраненную посылку по идентификатору.
    """
    repository = ParcelRepository(test_db_session)
    parcel = build_test_parcel()

    created_parcel = await repository.create(parcel)
    await test_db_session.commit()

    found_parcel = await repository.get_parcel_by_id(created_parcel.id)

    assert found_parcel is not None
    assert found_parcel.id == created_parcel.id
    assert found_parcel.name == "Телефон"
    assert found_parcel.parcel_type is not None
    assert found_parcel.parcel_type.name == "Электроника"


@pytest.mark.asyncio
async def test_get_parcel_by_id_returns_none_for_nonexistent_parcel(
    test_db_session,
) -> None:
    """
    Проверяет, что репозиторий возвращает None для несуществующей посылки.
    """
    repository = ParcelRepository(test_db_session)

    found_parcel = await repository.get_parcel_by_id(uuid4())

    assert found_parcel is None


@pytest.mark.asyncio
async def test_get_all_by_session_id_returns_only_session_parcels(
    test_db_session,
) -> None:
    """
    Проверяет, что репозиторий возвращает только посылки указанной сессии.
    """
    repository = ParcelRepository(test_db_session)

    test_db_session.add_all(
        [
            build_test_parcel(),
            build_test_parcel(
                name="Куртка",
                weight_kg="2.000",
                type_id=1,
                declared_value_usd="300.00",
            ),
            build_test_parcel(
                client_session_id="session-2",
                name="Ноутбук",
                weight_kg="3.000",
                declared_value_usd="2000.00",
            ),
        ]
    )
    await test_db_session.commit()

    parcels = await repository.get_all_by_session_id(
        client_session_id="session-1",
        page=1,
        page_size=10,
    )

    assert len(parcels) == 2
    assert {parcel.name for parcel in parcels} == {"Телефон", "Куртка"}


@pytest.mark.asyncio
async def test_get_all_by_session_id_filters_by_type_id(
    test_db_session,
) -> None:
    """
    Проверяет, что репозиторий фильтрует посылки по type_id.
    """
    repository = ParcelRepository(test_db_session)

    test_db_session.add_all(
        [
            build_test_parcel(),
            build_test_parcel(
                name="Куртка",
                weight_kg="2.000",
                type_id=1,
                declared_value_usd="300.00",
            ),
        ]
    )
    await test_db_session.commit()

    parcels = await repository.get_all_by_session_id(
        client_session_id="session-1",
        page=1,
        page_size=10,
        type_id=2,
    )

    assert len(parcels) == 1
    assert parcels[0].name == "Телефон"
    assert parcels[0].type_id == 2


@pytest.mark.asyncio
async def test_get_all_by_session_id_filters_by_has_delivery_cost(
    test_db_session,
) -> None:
    """
    Проверяет, что репозиторий фильтрует посылки
    по наличию рассчитанной стоимости доставки.
    """
    repository = ParcelRepository(test_db_session)

    test_db_session.add_all(
        [
            build_test_parcel(
                name="Обработанная",
                status=ParcelStatus.PROCESSED,
                delivery_cost_rub=Decimal("1500.50"),
            ),
            build_test_parcel(
                name="Необработанная",
                weight_kg=Decimal("2.000"),
                type_id=1,
                declared_value_usd=Decimal("300.00"),
            ),
        ]
    )
    await test_db_session.commit()

    parcels_with_cost = await repository.get_all_by_session_id(
        client_session_id="session-1",
        page=1,
        page_size=10,
        has_delivery_cost=True,
    )
    parcels_without_cost = await repository.get_all_by_session_id(
        client_session_id="session-1",
        page=1,
        page_size=10,
        has_delivery_cost=False,
    )

    assert len(parcels_with_cost) == 1
    assert parcels_with_cost[0].name == "Обработанная"

    assert len(parcels_without_cost) == 1
    assert parcels_without_cost[0].name == "Необработанная"


@pytest.mark.asyncio
async def test_get_all_by_session_id_applies_pagination(
    test_db_session,
) -> None:
    """
    Проверяет, что репозиторий корректно применяет пагинацию.
    """
    repository = ParcelRepository(test_db_session)

    test_db_session.add_all(
        [
            build_test_parcel(
                name="Посылка 1",
                weight_kg=Decimal("1.000"),
                type_id=1,
                declared_value_usd=Decimal("100.00"),
            ),
            build_test_parcel(
                name="Посылка 2",
                weight_kg=Decimal("2.000"),
                type_id=1,
                declared_value_usd=Decimal("200.00"),
            ),
            build_test_parcel(
                name="Посылка 3",
                weight_kg=Decimal("3.000"),
                type_id=3,
                declared_value_usd=Decimal("300.00"),
            ),
        ]
    )
    await test_db_session.commit()

    parcels = await repository.get_all_by_session_id(
        client_session_id="session-1",
        page=1,
        page_size=2,
    )

    assert len(parcels) == 2


@pytest.mark.asyncio
async def test_count_by_session_id_returns_total_number_of_session_parcels(
    test_db_session,
) -> None:
    """
    Проверяет, что репозиторий возвращает общее количество посылок указанной сессии.
    """
    repository = ParcelRepository(test_db_session)

    test_db_session.add_all(
        [
            build_test_parcel(),
            build_test_parcel(),
            build_test_parcel(client_session_id="session-2"),
        ]
    )
    await test_db_session.commit()

    total = await repository.count_by_session_id("session-1")

    assert total == 2


@pytest.mark.asyncio
async def test_assign_company_if_unassigned_returns_one_for_first_assignment(
    test_db_session,
) -> None:
    """
    Проверяет, что первая привязка компании к посылке успешно обновляет одну строку.
    """
    repository = ParcelRepository(test_db_session)
    parcel = build_test_parcel()

    created_parcel = await repository.create(parcel)
    await test_db_session.commit()

    updated_rows = await repository.assign_company_if_unassigned(
        parcel_id=created_parcel.id,
        company_id=10,
    )

    updated_parcel = await repository.get_parcel_by_id(created_parcel.id)

    assert updated_rows == 1
    assert updated_parcel is not None
    assert updated_parcel.company_id == 10


@pytest.mark.asyncio
async def test_assign_company_if_unassigned_returns_zero_for_taken_parcel(
    test_db_session,
) -> None:
    """
    Проверяет, что повторная привязка компании к уже занятой
    посылке не обновляет строки.
    """
    repository = ParcelRepository(test_db_session)
    parcel = build_test_parcel(
        company_id=10,
    )

    created_parcel = await repository.create(parcel)
    await test_db_session.commit()

    updated_rows = await repository.assign_company_if_unassigned(
        parcel_id=created_parcel.id,
        company_id=20,
    )

    updated_parcel = await repository.get_parcel_by_id(created_parcel.id)

    assert updated_rows == 0
    assert updated_parcel is not None
    assert updated_parcel.company_id == 10
