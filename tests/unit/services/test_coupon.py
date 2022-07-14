from decimal import Decimal

import pytest

from app.enums import CouponType
from app.services.coupon import CouponService


@pytest.mark.asyncio
async def test_calculate_total_purchase_nominal_discount(db_session):
    # GIVEN
    purchase_amount = Decimal(1000)
    discount_type = CouponType.NOMINAL
    discount_value = Decimal(10)
    max_amount = Decimal(0)
    coupon_service = CouponService(db_session)

    # WHEN
    total_purchase = coupon_service.calculate_total_purchase(
        purchase_amount,
        discount_type,
        discount_value,
        max_amount,
    )

    # THEN
    assert total_purchase == Decimal(990)


@pytest.mark.asyncio
async def test_calculate_total_purchase_nominal_discount_with_max_amount(
    db_session,
):
    # GIVEN
    purchase_amount = Decimal(1000)
    discount_type = CouponType.NOMINAL
    discount_value = Decimal(10)
    max_amount = Decimal(5)
    coupon_service = CouponService(db_session)

    # WHEN
    total_purchase = coupon_service.calculate_total_purchase(
        purchase_amount,
        discount_type,
        discount_value,
        max_amount,
    )

    # THEN
    assert total_purchase == Decimal(995)


@pytest.mark.asyncio
async def test_calculate_total_purchase_parcent_discount(db_session):
    # GIVEN
    purchase_amount = Decimal(1000)
    discount_type = CouponType.PERCENT
    discount_value = Decimal(10)
    max_amount = Decimal(0)
    coupon_service = CouponService(db_session)

    # WHEN
    total_purchase = coupon_service.calculate_total_purchase(
        purchase_amount,
        discount_type,
        discount_value,
        max_amount,
    )

    # THEN
    assert total_purchase == Decimal(900)


@pytest.mark.asyncio
async def test_calculate_total_purchase_parcent_discount_with_max_amount(
    db_session,
):
    # GIVEN
    purchase_amount = Decimal(1000)
    discount_type = CouponType.PERCENT
    discount_value = Decimal(10)
    max_amount = Decimal(10)
    coupon_service = CouponService(db_session)

    # WHEN
    total_purchase = coupon_service.calculate_total_purchase(
        purchase_amount,
        discount_type,
        discount_value,
        max_amount,
    )

    # THEN
    assert total_purchase == Decimal(990)
