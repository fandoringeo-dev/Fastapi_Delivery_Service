from pydantic import BaseModel


class ParcelTypeResponse(BaseModel):
    """
    Схема ответа с типом посылки.
    """

    id: int
    name: str
