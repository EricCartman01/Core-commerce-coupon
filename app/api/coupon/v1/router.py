from fastapi.routing import APIRouter

from app.api.coupon.v1.views import router

coupon_router = APIRouter()
coupon_router.include_router(router, prefix="/v1/coupons", tags=["Coupon V1"])
