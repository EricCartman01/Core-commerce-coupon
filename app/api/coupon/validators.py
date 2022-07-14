from datetime import datetime
from decimal import Decimal
from typing import Optional

import pytz

from app.settings import settings

utc = pytz.utc
local_timezone = pytz.timezone(settings.timezone)


def value_check(value: Decimal) -> str:
    return str(value.quantize(Decimal("1.00")))


def max_amount_check(max_amount: Decimal) -> Optional[str]:
    if max_amount is None:
        return max_amount
    return str(max_amount.quantize(Decimal("1.00")))


def min_purchase_amount_check(min_purchase_amount: Decimal) -> Optional[str]:
    if min_purchase_amount is None:
        return min_purchase_amount
    return str(min_purchase_amount.quantize(Decimal("1.00")))


def purchase_amount_with_discount_check(
    purchase_amount_with_discount: Decimal,
) -> str:
    return str(purchase_amount_with_discount.quantize(Decimal("1.00")))


def code_check(code: str) -> str:
    if code and not code.isalnum():
        raise ValueError("Code must be alphanumeric.")
    if code is not None and not len(code.strip()) > 0:
        raise ValueError("Code must not be empty.")
    return str(code).upper()


def valid_from_check(valid_from: datetime) -> datetime:
    return valid_from.astimezone(utc)


def valid_until_check(valid_until: datetime) -> datetime:
    return valid_until.astimezone(utc)


def utc_to_localtime(date: datetime) -> datetime:
    return date.astimezone(local_timezone)
