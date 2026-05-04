from fastapi import FastAPI

from app.api.v1.api_router import router as api_v1_router
from app.core.config import settings

app = FastAPI(
    title=settings.app_name,
    debug=settings.debug,
)

app.include_router(api_v1_router, prefix=settings.api_v1_prefix)
