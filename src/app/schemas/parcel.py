from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.common.enums import ParcelStatus
from app.schemas.parcel_type import ParcelTypeResponse


class ParcelCreateRequest(BaseModel):
    """
    POST_Request.
    Схема запроса на регистрацию посылки.
    """

    name: str = Field(min_length=1, max_length=255)
    weight_kg: Decimal = Field(gt=0)
    type_id: int = Field(gt=0)
    declared_value_usd: Decimal = Field(gt=0)


class ParcelCreateResponse(BaseModel):
    """
    POST_Response.
    Схема ответа на запрос создания посылки.
    """

    id: UUID
    status: ParcelStatus

    model_config = ConfigDict(from_attributes=True)


class ParcelItemResponse(BaseModel):
    """
    GET_Response.
    Схема ответа с данными о посылке.
    """

    id: UUID
    name: str
    status: ParcelStatus
    weight_kg: Decimal
    parcel_type: ParcelTypeResponse
    declared_value_usd: Decimal
    delivery_cost_rub: Decimal | None
    company_id: int | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ParcelListResponse(BaseModel):
    """
    GET_Response.
    Схема ответа со списком посылок и пагинацией.
    """

    items: list[ParcelItemResponse]
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


class ParcelAssignCompanyRequest(BaseModel):
    """
    POST_Request.
    Схема запроса на привязку транспортной компании к посылке.
    """

    company_id: int = Field(gt=0, description="Идентификатор транспортной компании.")
