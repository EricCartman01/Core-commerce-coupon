from fastapi.routing import APIRouter

from app.api.coupon.v2.views import router

coupon_router = APIRouter()
coupon_router.include_router(router, prefix="/v2/coupons", tags=["Coupon V2"])
