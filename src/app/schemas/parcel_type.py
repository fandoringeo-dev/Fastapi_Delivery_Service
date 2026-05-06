from pydantic import BaseModel, ConfigDict


class ParcelTypeResponse(BaseModel):
    """
    Схема ответа с типом посылки.
    """

    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)
