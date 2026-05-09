from uuid import UUID

from fastapi import APIRouter, Depends, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.cookie_session import create_session_id, get_session_id, set_session_cookie
from app.db.dependencies import get_db_session
from app.db.rabbitmq import get_rabbitmq_connection
from app.repositories.parcel import ParcelRepository
from app.schemas.parcel import (
    ParcelAssignCompanyRequest,
    ParcelCreateRequest,
    ParcelCreateResponse,
    ParcelItemResponse,
    ParcelListQueryParams,
    ParcelListResponse,
)
from app.services.parcel import ParcelService
from app.services.rabbitmq_producer import RabbitMQProducerService

router = APIRouter(
    prefix="/parcels",
)


@router.post(
    "/",
    response_model=ParcelCreateResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_parcel(
    parcel_data: ParcelCreateRequest,
    request: Request,
    response: Response,
    session: AsyncSession = Depends(get_db_session),
) -> ParcelCreateResponse:
    """
    Регистрирует новую посылку.
    """
    client_session_id = get_session_id(request)
    is_new_session = client_session_id is None

    if client_session_id is None:
        client_session_id = create_session_id()

    repository = ParcelRepository(session)
    rabbitmq_connection = await get_rabbitmq_connection()
    producer = RabbitMQProducerService(rabbitmq_connection)
    service = ParcelService(repository, producer)

    parcel = await service.create_parcel(
        parcel_data=parcel_data,
        client_session_id=client_session_id,
    )

    if is_new_session:
        set_session_cookie(response, client_session_id)

    return parcel


@router.get(
    "/{parcel_id}",
    status_code=status.HTTP_200_OK,
)
async def read_parcel(
    parcel_id: UUID,
    request: Request,
    session: AsyncSession = Depends(get_db_session),
) -> ParcelItemResponse:
    """
    Возвращает посылку по id.
    """
    client_session_id = get_session_id(request)
    repository = ParcelRepository(session)
    service = ParcelService(repository)
    parcel = await service.read_parcel_by_id(
        parcel_id=parcel_id,
        client_session_id=client_session_id,
    )
    return parcel


@router.get(
    "/",
    response_model=ParcelListResponse,
    status_code=status.HTTP_200_OK,
)
async def read_parcels(
    request: Request,
    query_params: ParcelListQueryParams = Depends(),
    session: AsyncSession = Depends(get_db_session),
) -> ParcelListResponse:
    """
    Возвращает список посылок пользователя с учетом фильтрации и пагинации.
    """
    client_session_id = get_session_id(request)

    repository = ParcelRepository(session)
    service = ParcelService(repository)

    return await service.get_parcels(
        client_session_id=client_session_id,
        query_params=query_params,
    )


@router.post(
    "/{parcel_id}/assign-company",
    status_code=status.HTTP_200_OK,
)
async def assign_company_to_parcel(
    parcel_id: UUID,
    request_data: ParcelAssignCompanyRequest,
    session: AsyncSession = Depends(get_db_session),
) -> None:
    """
    Привязывает транспортную компанию к посылке.
    """
    repository = ParcelRepository(session)
    service = ParcelService(repository)

    await service.assign_company_to_parcel(
        parcel_id=parcel_id,
        company_id=request_data.company_id,
    )
