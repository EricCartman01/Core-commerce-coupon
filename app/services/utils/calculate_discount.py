from decimal import Decimal

from app.enums import CouponType


def calculate_discount(
    purchase_amount: Decimal,
    discount_type: str,
    discount_value: Decimal,
    max_amount: Decimal,
) -> Decimal:
    """
    :param purchase_amount: total purchase value.
    :param discount_type: type discount (percent, nominal).
    :param discount_value: value of discount.
    :param max_amount: max value of discount.
    :return: discount value.
    """

    if CouponType.NOMINAL == discount_type:
        discount_value = min(purchase_amount, discount_value)

    if CouponType.PERCENT == discount_type:
        discount_value = Decimal(purchase_amount) * Decimal(
            discount_value / 100
        )

    if max_amount and discount_value > max_amount:
        discount_value = max_amount

    return discount_value
