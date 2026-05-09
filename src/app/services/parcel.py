from uuid import UUID

from aio_pika.exceptions import AMQPException
from fastapi import HTTPException, status
from loguru import logger

from app.common.enums import ParcelStatus
from app.models.parcel import Parcel
from app.repositories.parcel import ParcelRepository
from app.repositories.parcel_type import ParcelTypeRepository
from app.schemas.parcel import (
    ParcelCreateRequest,
    ParcelListQueryParams,
    ParcelListResponse,
)
from app.services.rabbitmq_producer import RabbitMQProducerService


class ParcelService:
    """
    Сервис для работы с посылками.
    """

    def __init__(
        self,
        repository: ParcelRepository,
        producer: RabbitMQProducerService | None = None,
    ) -> None:
        """
        Инициализирует сервис.

        :param repository: Репозиторий посылок.
        :param producer: Producer RabbitMQ для публикации задачи.
        """
        self.repository = repository
        self.parcel_type_repository = ParcelTypeRepository(repository.session)
        self.producer = producer

    async def create_parcel(
        self,
        parcel_data: ParcelCreateRequest,
        client_session_id: str,
    ) -> Parcel:
        """
        Регистрирует новую посылку.

        :param parcel_data: Данные для регистрации посылки.
        :param client_session_id: Идентификатор клиентской сессии.
        :return: Созданная посылка.
        """
        parcel_type = await self.parcel_type_repository.get_parcel_type(
            parcel_data.type_id
        )

        if not parcel_type:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Указанный тип посылки не существует",
            )

        parcel = Parcel(
            client_session_id=client_session_id,
            name=parcel_data.name,
            status=ParcelStatus.PENDING,
            weight_kg=parcel_data.weight_kg,
            type_id=parcel_data.type_id,
            declared_value_usd=parcel_data.declared_value_usd,
        )

        parcel = await self.repository.create(parcel)
        await self.repository.session.commit()

        logger.info(
            "Посылка зарегистрирована: parcel_id={}, client_session_id={}, status={}",
            parcel.id,
            client_session_id,
            parcel.status,
        )

        try:
            await self.producer.publish_parcel_created(parcel.id)
        except AMQPException:
            logger.exception(
                "Не удалось отправить сообщение о посылке в RabbitMQ: parcel_id={}",
                parcel.id,
            )

        return parcel

    async def read_parcel_by_id(
        self,
        parcel_id: UUID,
        client_session_id: str | None,
    ) -> Parcel:
        """
        Возвращает данные по посылке по id c проверкой клиентской сессии
        """
        if client_session_id is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Отсутствует идентификатор сессии.",
            )

        parcel_db = await self.repository.get_parcel_by_id(parcel_id=parcel_id)
        if parcel_db is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Посылка с указанным id не существует",
            )

        if parcel_db.client_session_id != client_session_id:
            logger.warning(
                "Попытка доступа к чужой посылке: parcel_id={}, client_session_id={}",
                parcel_id,
                client_session_id,
            )

            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Посылка с указанным id не принадлежит пользователю",
            )

        return parcel_db

    async def get_parcels(
        self,
        client_session_id: str | None,
        query_params: ParcelListQueryParams,
    ) -> ParcelListResponse:
        """
        Возвращает список посылок пользователя с учетом фильтрации и пагинации.

        :param client_session_id: Идентификатор клиентской сессии.
        :param query_params: Параметры фильтрации и пагинации.
        :return: Список посылок с пагинацией.
        """
        if client_session_id is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Отсутствует идентификатор сессии.",
            )

        items = await self.repository.get_all_by_session_id(
            client_session_id=client_session_id,
            page=query_params.page,
            page_size=query_params.page_size,
            type_id=query_params.type_id,
            has_delivery_cost=query_params.has_delivery_cost,
        )

        total = await self.repository.count_by_session_id(
            client_session_id=client_session_id,
            type_id=query_params.type_id,
            has_delivery_cost=query_params.has_delivery_cost,
        )

        return ParcelListResponse(
            items=items,
            page=query_params.page,
            page_size=query_params.page_size,
            total=total,
        )

    async def assign_company_to_parcel(
        self,
        parcel_id: UUID,
        company_id: int,
    ) -> None:
        """
        Привязывает транспортную компанию к посылке.

        :param parcel_id: Идентификатор посылки.
        :param company_id: Идентификатор транспортной компании.
        """
        parcel = await self.repository.get_parcel_by_id(parcel_id=parcel_id)
        if parcel is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Посылка с указанным id не существует",
            )

        updated_rows = await self.repository.assign_company_if_unassigned(
            parcel_id=parcel_id,
            company_id=company_id,
        )

        if not updated_rows:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Посылка уже привязана к транспортной компании",
            )

        logger.info(
            "Транспортная компания привязана к посылке: parcel_id={}, company_id={}",
            parcel_id,
            company_id,
        )
