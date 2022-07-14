from fastapi.routing import APIRouter

from app.api import docs, healthcheck
from app.api.coupon import coupon

api_router = APIRouter()
api_router.include_router(docs.router)
api_router.include_router(healthcheck.router, tags=["Healthcheck"])
api_router.include_router(coupon)
