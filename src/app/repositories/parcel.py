from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.parcel import Parcel


class ParcelRepository:
    """
    Репозиторий для работы с посылками.
    """

    def __init__(self, session: AsyncSession) -> None:
        """
        Инициализирует репозиторий.
        """
        self.session = session

    async def create(self, parcel: Parcel) -> Parcel:
        """
        Сохраняет посылку в базе данных.
        """
        self.session.add(parcel)
        await self.session.flush()
        await self.session.refresh(parcel)
        return parcel

    async def get_parcel_by_id(
        self,
        parcel_id: UUID,
    ) -> Parcel | None:
        """
        Возвращает посылку по идентификатору.

        :param parcel_id: Идентификатор посылки.
        :return: Посылка или None.
        """
        stmt = (
            select(Parcel)
            .options(selectinload(Parcel.parcel_type))
            .where(
                Parcel.id == parcel_id,
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all_by_session_id(
        self,
        client_session_id: str,
        page: int,
        page_size: int,
        type_id: int | None = None,
        has_delivery_cost: bool | None = None,
    ) -> list[Parcel]:
        """
        Возвращает список посылок пользователя с учетом фильтрации и пагинации.

        :param client_session_id: Идентификатор клиентской сессии.
        :param page: Номер страницы.
        :param page_size: Размер страницы.
        :param type_id: Идентификатор типа посылки.
        :param has_delivery_cost: Признак наличия рассчитанной стоимости доставки.
        :return: Список посылок.
        """
        stmt = (
            select(Parcel)
            .options(selectinload(Parcel.parcel_type))
            .where(Parcel.client_session_id == client_session_id)
            .order_by(Parcel.created_at.desc())
        )

        if type_id is not None:
            stmt = stmt.where(Parcel.type_id == type_id)

        if has_delivery_cost is True:
            stmt = stmt.where(Parcel.delivery_cost_rub.is_not(None))
        elif has_delivery_cost is False:
            stmt = stmt.where(Parcel.delivery_cost_rub.is_(None))

        stmt = stmt.offset((page - 1) * page_size).limit(page_size)

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def count_by_session_id(
        self,
        client_session_id: str,
        type_id: int | None = None,
        has_delivery_cost: bool | None = None,
    ) -> int:
        """
        Возвращает общее количество посылок пользователя с учетом фильтрации.

        :param client_session_id: Идентификатор клиентской сессии.
        :param type_id: Идентификатор типа посылки.
        :param has_delivery_cost: Признак наличия рассчитанной стоимости доставки.
        :return: Общее количество посылок.
        """
        stmt = select(func.count(Parcel.id)).where(
            Parcel.client_session_id == client_session_id
        )

        if type_id is not None:
            stmt = stmt.where(Parcel.type_id == type_id)

        if has_delivery_cost is True:
            stmt = stmt.where(Parcel.delivery_cost_rub.is_not(None))
        elif has_delivery_cost is False:
            stmt = stmt.where(Parcel.delivery_cost_rub.is_(None))

        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def assign_company_if_unassigned(
        self,
        parcel_id: UUID,
        company_id: int,
    ) -> int:
        """
        Привязывает транспортную компанию к посылке, если она еще не привязана.

        :param parcel_id: Идентификатор посылки.
        :param company_id: Идентификатор транспортной компании.
        :return: Количество обновленных строк.
        """
        stmt = (
            update(Parcel)
            .where(
                Parcel.id == parcel_id,
                Parcel.company_id.is_(None),
            )
            .values(company_id=company_id)
        )

        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.rowcount
