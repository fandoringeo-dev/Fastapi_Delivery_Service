from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.parcel_type import ParcelType


class ParcelTypeRepository:
    """
    Репозиторий для работы с типами посылок.
    """

    def __init__(self, session: AsyncSession) -> None:
        """
        Инициализирует репозиторий.
        """
        self.session = session

    async def get_all(self) -> list[ParcelType]:
        """
        Возвращает список всех типов посылок.
        """
        stmt = select(ParcelType).order_by(ParcelType.id)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_parcel_type(self, type_id: int) -> ParcelType | None:
        """
        Возвращает тип посылки.
        """
        stmt = select(ParcelType).where(ParcelType.id == type_id)
        parcel_type = await self.session.execute(stmt)
        return parcel_type.scalar()
