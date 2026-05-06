import uuid

from fastapi import Request, Response

SESSION_COOKIE_NAME = "client_session_id"


def get_session_id(request: Request) -> str | None:
    """
    Возвращает идентификатор клиентской сессии из cookie.

    :param request: Объект запроса FastAPI.
    :return: Идентификатор сессии или None.
    """
    return request.cookies.get(SESSION_COOKIE_NAME)


def create_session_id() -> str:
    """
    Создает новый идентификатор клиентской сессии.

    :return: Новый идентификатор сессии.
    """
    return str(uuid.uuid4())


def set_session_cookie(response: Response, session_id: str) -> None:
    """
    Устанавливает cookie с идентификатором клиентской сессии.

    :param response: Объект ответа FastAPI.
    :param session_id: Идентификатор клиентской сессии.
    """
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=session_id,
        httponly=True,
        samesite="lax",
    )
