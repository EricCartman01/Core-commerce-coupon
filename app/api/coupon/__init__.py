"""Routes for swagger and redoc."""

from app.api.coupon.router import coupon_router as coupon

__all__ = ["coupon"]
