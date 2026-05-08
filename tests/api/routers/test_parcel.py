from decimal import Decimal
from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.api.cookie_session import SESSION_COOKIE_NAME
from app.common.enums import ParcelStatus
from app.models.parcel import Parcel
from tests.factories import (
    build_create_parcel_payload,
    create_parcel,
)


@pytest.mark.asyncio
async def test_create_parcel_returns_status_code_201(
    test_client: AsyncClient,
) -> None:
    """
    Проверяет, что endpoint регистрации посылки возвращает статус-код 201.
    """
    response = await test_client.post(
        "/api/v1/parcels/",
        json=build_create_parcel_payload(),
    )

    assert response.status_code == 201


@pytest.mark.asyncio
async def test_create_parcel_returns_created_parcel_id_and_pending_status(
    test_client: AsyncClient,
) -> None:
    """
    Проверяет, что endpoint регистрации посылки возвращает id и статус pending.
    """
    response = await test_client.post(
        "/api/v1/parcels/",
        json=build_create_parcel_payload(),
    )

    assert response.json()["id"]
    assert response.json()["status"] == "pending"


@pytest.mark.asyncio
async def test_create_parcel_sets_session_cookie_for_new_client(
    test_client: AsyncClient,
) -> None:
    """
    Проверяет, что при первой регистрации посылки клиенту
    устанавливается session cookie.
    """
    response = await test_client.post(
        "/api/v1/parcels/",
        json=build_create_parcel_payload(),
    )

    assert SESSION_COOKIE_NAME in response.cookies
    assert response.cookies.get(SESSION_COOKIE_NAME) is not None


@pytest.mark.asyncio
async def test_create_parcel_with_invalid_type_returns_status_code_400(
    test_client: AsyncClient,
) -> None:
    """
    Проверяет, что регистрация посылки с несуществующим типом возвращает статус-код 400.
    """
    response = await test_client.post(
        "/api/v1/parcels/",
        json=build_create_parcel_payload(type_id=999),
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Указанный тип посылки не существует"


@pytest.mark.asyncio
async def test_create_parcel_with_zero_weight_returns_status_code_422(
    test_client: AsyncClient,
) -> None:
    """
    Проверяет, что регистрация посылки с нулевым весом возвращает статус-код 422.
    """
    response = await test_client.post(
        "/api/v1/parcels/",
        json=build_create_parcel_payload(weight_kg="0"),
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_parcel_with_empty_name_returns_status_code_422(
    test_client: AsyncClient,
) -> None:
    """
    Проверяет, что регистрация посылки с пустым именем возвращает статус-код 422.
    """
    response = await test_client.post(
        "/api/v1/parcels/",
        json=build_create_parcel_payload(name=""),
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_read_parcel_returns_status_code_200_for_owner_session(
    test_client: AsyncClient,
) -> None:
    """
    Проверяет, что владелец посылки может получить ее по id.
    """
    created = await create_parcel(test_client)

    response = await test_client.get(f"/api/v1/parcels/{created['id']}")

    assert response.status_code == 200


@pytest.mark.asyncio
async def test_read_parcel_returns_parcel_data_in_expected_format(
    test_client: AsyncClient,
) -> None:
    """
    Проверяет, что endpoint получения посылки по id
    возвращает данные в ожидаемом формате.
    """
    created = await create_parcel(test_client)

    response = await test_client.get(f"/api/v1/parcels/{created['id']}")
    data = response.json()

    assert data["id"] == created["id"]
    assert data["name"] == "Телефон"
    assert data["status"] == "pending"
    assert data["weight_kg"] == "1.500"
    assert data["parcel_type"] == {"id": 2, "name": "Электроника"}
    assert data["declared_value_usd"] == "1000.00"
    assert data["delivery_cost_rub"] is None
    assert data["company_id"] is None
    assert "created_at" in data


@pytest.mark.asyncio
async def test_read_parcel_without_session_cookie_returns_status_code_400(
    test_client: AsyncClient,
) -> None:
    """
    Проверяет, что запрос посылки без session cookie возвращает статус-код 400.
    """
    response = await test_client.get(f"/api/v1/parcels/{uuid4()}")

    assert response.status_code == 400
    assert response.json()["detail"] == "Отсутствует идентификатор сессии."


@pytest.mark.asyncio
async def test_read_nonexistent_parcel_returns_status_code_404(
    test_client: AsyncClient,
) -> None:
    """
    Проверяет, что запрос несуществующей посылки возвращает статус-код 404.
    """
    await create_parcel(test_client)

    response = await test_client.get(f"/api/v1/parcels/{uuid4()}")

    assert response.status_code == 404
    assert response.json()["detail"] == "Посылка с указанным id не существует"


@pytest.mark.asyncio
async def test_read_foreign_parcel_returns_status_code_403(
    test_client: AsyncClient,
) -> None:
    """
    Проверяет, что пользователь не может получить чужую посылку.
    """
    created = await create_parcel(test_client)

    test_client.cookies.clear()
    test_client.cookies.set(SESSION_COOKIE_NAME, "foreign-session-id")

    response = await test_client.get(f"/api/v1/parcels/{created['id']}")

    assert response.status_code == 403
    assert (
        response.json()["detail"]
        == "Посылка с указанным id не принадлежит пользователю"
    )


@pytest.mark.asyncio
async def test_read_parcels_returns_status_code_200(
    test_client: AsyncClient,
) -> None:
    """
    Проверяет, что endpoint списка посылок возвращает статус-код 200.
    """
    await create_parcel(test_client)

    response = await test_client.get("/api/v1/parcels/")

    assert response.status_code == 200


@pytest.mark.asyncio
async def test_read_parcels_returns_only_current_session_parcels(
    test_client: AsyncClient,
) -> None:
    """
    Проверяет, что endpoint списка возвращает только посылки текущей сессии.
    """
    await create_parcel(test_client, name="Посылка 1")
    await create_parcel(test_client, name="Посылка 2")

    response = await test_client.get("/api/v1/parcels/")
    data = response.json()

    assert data["total"] == 2
    assert len(data["items"]) == 2
    assert {item["name"] for item in data["items"]} == {"Посылка 1", "Посылка 2"}


@pytest.mark.asyncio
async def test_read_parcels_without_session_cookie_returns_status_code_400(
    test_client: AsyncClient,
) -> None:
    """
    Проверяет, что запрос списка посылок без session cookie возвращает статус-код 400.
    """
    response = await test_client.get("/api/v1/parcels/")

    assert response.status_code == 400
    assert response.json()["detail"] == "Отсутствует идентификатор сессии."


@pytest.mark.asyncio
async def test_read_parcels_filters_by_type_id(
    test_client: AsyncClient,
) -> None:
    """
    Проверяет, что endpoint списка фильтрует посылки по type_id.
    """
    await create_parcel(test_client, name="Телефон", type_id=2)
    await create_parcel(test_client, name="Куртка", type_id=1)

    response = await test_client.get("/api/v1/parcels/?type_id=2")
    data = response.json()

    assert data["total"] == 1
    assert len(data["items"]) == 1
    assert data["items"][0]["name"] == "Телефон"
    assert data["items"][0]["parcel_type"] == {"id": 2, "name": "Электроника"}


@pytest.mark.asyncio
async def test_read_parcels_filters_by_has_delivery_cost(
    test_client: AsyncClient,
    test_db_session,
) -> None:
    """
    Проверяет, что endpoint списка фильтрует посылки
    по наличию рассчитанной стоимости доставки.
    """
    first = await create_parcel(test_client, name="Обработанная")
    await create_parcel(test_client, name="Необработанная")

    parcel = await test_db_session.scalar(
        select(Parcel).where(Parcel.id == first["id"])
    )
    parcel.delivery_cost_rub = Decimal("1500.50")
    parcel.status = ParcelStatus.PROCESSED
    await test_db_session.commit()

    response = await test_client.get("/api/v1/parcels/?has_delivery_cost=true")
    data = response.json()

    assert data["total"] == 1
    assert len(data["items"]) == 1
    assert data["items"][0]["name"] == "Обработанная"
    assert data["items"][0]["delivery_cost_rub"] == "1500.50"

    response = await test_client.get("/api/v1/parcels/?has_delivery_cost=false")
    data = response.json()

    assert data["total"] == 1
    assert len(data["items"]) == 1
    assert data["items"][0]["name"] == "Необработанная"
    assert data["items"][0]["delivery_cost_rub"] is None


@pytest.mark.asyncio
async def test_read_parcels_applies_pagination(
    test_client: AsyncClient,
) -> None:
    """
    Проверяет, что endpoint списка корректно применяет пагинацию.
    """
    await create_parcel(test_client, name="Посылка 1")
    await create_parcel(test_client, name="Посылка 2")
    await create_parcel(test_client, name="Посылка 3")

    response = await test_client.get("/api/v1/parcels/?page=1&page_size=2")
    data = response.json()

    assert data["page"] == 1
    assert data["page_size"] == 2
    assert data["total"] == 3
    assert len(data["items"]) == 2


@pytest.mark.asyncio
async def test_assign_company_to_parcel_returns_status_code_200(
    test_client: AsyncClient,
) -> None:
    """
    Проверяет, что первая транспортная компания может успешно привязаться к посылке.
    """
    created = await create_parcel(test_client)

    response = await test_client.post(
        f"/api/v1/parcels/{created['id']}/assign-company",
        json={"company_id": 10},
    )

    assert response.status_code == 200


@pytest.mark.asyncio
async def test_assign_company_to_parcel_updates_company_id(
    test_client: AsyncClient,
) -> None:
    """
    Проверяет, что привязка транспортной компании сохраняет company_id у посылки.
    """
    created = await create_parcel(test_client)

    await test_client.post(
        f"/api/v1/parcels/{created['id']}/assign-company",
        json={"company_id": 10},
    )

    response = await test_client.get(f"/api/v1/parcels/{created['id']}")
    data = response.json()

    assert data["company_id"] == 10


@pytest.mark.asyncio
async def test_assign_company_to_nonexistent_parcel_returns_status_code_404(
    test_client: AsyncClient,
) -> None:
    """
    Проверяет, что привязка компании к несуществующей посылке возвращает статус-код 404.
    """
    response = await test_client.post(
        f"/api/v1/parcels/{uuid4()}/assign-company",
        json={"company_id": 10},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Посылка с указанным id не существует"


@pytest.mark.asyncio
async def test_assign_company_to_taken_parcel_returns_status_code_409(
    test_client: AsyncClient,
) -> None:
    """
    Проверяет, что повторная привязка компании к уже занятой
    посылке возвращает статус-код 409.
    """
    created = await create_parcel(test_client)

    first_response = await test_client.post(
        f"/api/v1/parcels/{created['id']}/assign-company",
        json={"company_id": 10},
    )
    second_response = await test_client.post(
        f"/api/v1/parcels/{created['id']}/assign-company",
        json={"company_id": 20},
    )

    assert first_response.status_code == 200
    assert second_response.status_code == 409
    assert (
        second_response.json()["detail"]
        == "Посылка уже привязана к транспортной компании"
    )


@pytest.mark.asyncio
async def test_assign_company_with_non_positive_company_id_returns_status_code_422(
    test_client: AsyncClient,
) -> None:
    """
    Проверяет, что привязка компании с неположительным
    company_id возвращает статус-код 422.
    """
    created = await create_parcel(test_client)

    response = await test_client.post(
        f"/api/v1/parcels/{created['id']}/assign-company",
        json={"company_id": 0},
    )

    assert response.status_code == 422
