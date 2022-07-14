from fastapi.routing import APIRouter

from app.api.coupon.v1.router import coupon_router as coupon_v1
from app.api.coupon.v2.router import coupon_router as coupon_v2

coupon_router = APIRouter()
coupon_router.include_router(coupon_v1)
coupon_router.include_router(coupon_v2)
