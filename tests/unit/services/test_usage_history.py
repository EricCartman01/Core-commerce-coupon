from decimal import Decimal

import pytest

from app.enums import CouponType
from app.services.usage_history import UsageHistoryService
from app.services.utils.calculate_discount import calculate_discount


@pytest.mark.asyncio
async def test_calculate_discount_nominal():
    # GIVEN
    purchase_amount = Decimal(1000)
    discount_type = CouponType.NOMINAL
    discount_value = Decimal(10)
    max_amount = Decimal(0)

    # WHEN
    total_purchase = calculate_discount(
        purchase_amount,
        discount_type,
        discount_value,
        max_amount,
    )

    # THEN
    assert total_purchase == Decimal(10)


@pytest.mark.asyncio
async def test_calculate_discount_nominal_with_max_amount():
    # GIVEN
    purchase_amount = Decimal(1000)
    discount_type = CouponType.NOMINAL
    discount_value = Decimal(20)
    max_amount = Decimal(10)

    # WHEN
    total_purchase = calculate_discount(
        purchase_amount,
        discount_type,
        discount_value,
        max_amount,
    )

    # THEN
    assert total_purchase == max_amount


@pytest.mark.asyncio
async def test_calculate_discount_percent():
    # GIVEN
    purchase_amount = Decimal(1000)
    discount_type = CouponType.PERCENT
    discount_value = Decimal(10)
    max_amount = Decimal(0)

    # WHEN
    total_purchase = calculate_discount(
        purchase_amount,
        discount_type,
        discount_value,
        max_amount,
    )

    # THEN
    assert total_purchase == Decimal(100)


@pytest.mark.asyncio
async def test_calculate_discount_percentwith_max_amount():
    # GIVEN
    purchase_amount = Decimal(1000)
    discount_type = CouponType.PERCENT
    discount_value = Decimal(10)
    max_amount = Decimal(10)

    # WHEN
    total_purchase = calculate_discount(
        purchase_amount,
        discount_type,
        discount_value,
        max_amount,
    )

    # THEN
    assert total_purchase == Decimal(10)
