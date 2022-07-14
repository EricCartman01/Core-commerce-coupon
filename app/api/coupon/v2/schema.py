from decimal import Decimal

from pydantic import BaseModel
from pydantic.class_validators import validator

from app.api.coupon.validators import code_check


class MessageError(BaseModel):
    error_code: str
    error_message: str


class CouponReservedInputSchema(BaseModel):
    code: str
    transaction_id: str
    customer_key: str
    purchase_amount: Decimal
    first_purchase: bool

    _code_check = validator("code", allow_reuse=True)(code_check)


class CouponUnreservedConfirmedInputSchema(BaseModel):
    code: str
    transaction_id: str

    _code_check = validator("code", allow_reuse=True)(code_check)
