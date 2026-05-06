from fastapi import APIRouter

from app.api.v1.routers.health import router as health_router
from app.api.v1.routers.parcel import router as parcel_router
from app.api.v1.routers.parcel_type import router as parcel_type_router

router = APIRouter()
router.include_router(health_router, tags=["Health"])
router.include_router(parcel_type_router, tags=["Parcel type"])
router.include_router(parcel_router, tags=["Parcel"])
