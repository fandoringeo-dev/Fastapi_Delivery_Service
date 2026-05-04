from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.common.enums import ParcelStatus


class ParcelCreateRequest(BaseModel):
    """
    Схема запроса на регистрацию посылки.
    """

    name: str = Field(min_length=1, max_length=255)
    weight_kg: Decimal = Field(gt=0)
    type_id: int = Field(gt=0)
    declared_value_usd: Decimal = Field(gt=0)


class ParcelResponse(BaseModel):
    """
    Схема детального ответа по посылке.
    """

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    status: ParcelStatus
    weight_kg: Decimal
    type_id: int
    type_name: str
    declared_value_usd: Decimal
    delivery_cost_rub: Decimal | None
    company_id: int | None
    created_at: datetime
    updated_at: datetime


class ParcelListItemResponse(BaseModel):
    """
    Схема элемента списка посылок.
    """

    id: UUID
    name: str
    status: ParcelStatus
    type_id: int
    type_name: str
    delivery_cost_rub: Decimal | None
    created_at: datetime


class ParcelListResponse(BaseModel):
    """
    Схема ответа со списком посылок и пагинацией.
    """

    items: list[ParcelListItemResponse]
    page: int
    page_size: int
    total: int


class ParcelListQueryParams(BaseModel):
    """
    Схема параметров фильтрации и пагинации списка посылок.
    """

    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=10, ge=1, le=100)
    type_id: int | None = Field(default=None, gt=0)
    has_delivery_cost: bool | None = None
