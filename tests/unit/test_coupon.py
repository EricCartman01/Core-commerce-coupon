import pytest
import pytz
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.api.coupon.v1.schema import CouponSchema, CouponSchemaBase
from app.models.coupon import Coupon
from app.settings import settings


@pytest.mark.asyncio
async def test_coupon_usage_history_relationship_empty(
    coupons_factory,
    db_session,
):
    # GIVEN
    raw = await db_session.execute(
        select(Coupon)
        .options(selectinload(Coupon.usage_histories))
        .where(Coupon.coupon_id == coupons_factory[0].coupon_id),
    )
    coupon = raw.scalar_one()
    # WHEN
    # THEN
    r = coupon.usage_histories
    assert r == []


@pytest.mark.asyncio
async def test_get_usage_histories_from_coupon_with_relationship(
    usage_histories_factory,
    db_session,
):
    raw = await db_session.execute(
        select(Coupon)
        .options(selectinload(Coupon.usage_histories))
        .where(Coupon.coupon_id == usage_histories_factory[0].coupon_id),
    )
    coupon = raw.scalar_one()
    histories = coupon.usage_histories
    assert len(histories) == 2
    assert histories[0].id == usage_histories_factory[0].id
    assert histories[1].id == usage_histories_factory[1].id


@pytest.mark.asyncio
async def test_coupon_accumulated_value(usage_histories_factory, db_session):
    raw = await db_session.execute(
        select(Coupon)
        .options(selectinload(Coupon.usage_histories))
        .where(Coupon.coupon_id == usage_histories_factory[0].coupon_id),
    )
    coupon = raw.scalar_one()
    histories = coupon.usage_histories
    assert len(histories) == 2
    assert histories[0].id == usage_histories_factory[0].id
    assert histories[1].id == usage_histories_factory[1].id

    expected_discount = (
        usage_histories_factory[0].discount_amount
        + usage_histories_factory[1].discount_amount
    )

    assert coupon.accumulated_value == expected_discount


@pytest.mark.asyncio
async def test_coupon_input_timezone(coupons_factory, db_session):
    coupon = coupons_factory[0]

    coupon_schema = CouponSchemaBase(
        description=coupon.description,
        code=coupon.code,
        customer_key=coupon.customer_key,
        valid_from=coupon.valid_from,
        valid_until=coupon.valid_until,
        max_usage=coupon.max_usage,
        type=coupon.type,
        value=coupon.value,
        max_amount=coupon.max_amount,
        first_purchase=coupon.first_purchase,
        limit_per_customer=coupon.limit_per_customer,
        active=coupon.active,
        budget=coupon.budget,
        user_create=coupon.user_create,
    )

    assert coupon_schema.valid_from.tzinfo.zone == pytz.utc.zone
    assert coupon_schema.valid_until.tzinfo.zone == pytz.utc.zone


@pytest.mark.asyncio
async def test_coupon_output_timezone(coupons_factory, db_session):
    coupon = coupons_factory[0]

    coupon_schema = CouponSchema(
        description=coupon.description,
        code=coupon.code,
        customer_key=coupon.customer_key,
        valid_from=coupon.valid_from,
        valid_until=coupon.valid_until,
        max_usage=coupon.max_usage,
        type=coupon.type,
        max_amount=coupon.max_amount,
        first_purchase=coupon.first_purchase,
        limit_per_customer=coupon.limit_per_customer,
        active=coupon.active,
        budget=coupon.budget,
    )

    assert coupon_schema.valid_from.tzinfo.zone == settings.timezone
    assert coupon_schema.valid_until.tzinfo.zone == settings.timezone
