from app.models.parcel_type import ParcelType
from app.repositories.parcel_type import ParcelTypeRepository


class ParcelTypeService:
    """
    Сервис для работы с типами посылок.
    """

    def __init__(self, repository: ParcelTypeRepository) -> None:
        """
        Инициализирует сервис.
        """
        self.repository = repository

    async def get_all(self) -> list[ParcelType]:
        """
        Возвращает список всех типов посылок.
        """
        return await self.repository.get_all()
