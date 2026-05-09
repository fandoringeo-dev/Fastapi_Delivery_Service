from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.dependencies import get_db_session
from app.repositories.parcel_type import ParcelTypeRepository
from app.schemas.parcel_type import ParcelTypeResponse
from app.services.parcel_type import ParcelTypeService

router = APIRouter()


@router.get("/parcel-types", response_model=list[ParcelTypeResponse])
async def get_parcel_types(
    session: AsyncSession = Depends(get_db_session),
) -> list[ParcelTypeResponse]:
    """
    Возвращает список всех типов посылок.
    """
    repository = ParcelTypeRepository(session)
    service = ParcelTypeService(repository)
    parcel_types = await service.get_all()
    return parcel_types
