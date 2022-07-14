from datetime import datetime

import pytest
from fastapi import status
from httpx import AsyncClient
from sqlalchemy.orm import selectinload
from sqlalchemy.sql.expression import select

from app.models.coupon import Coupon, UsageHistory

VALID_DATE_ISOFORMAT = datetime.now().isoformat()


@pytest.mark.asyncio
async def test_should_confirme_usage_coupon(
    async_client: AsyncClient, coupons_factory, db_session
):
    # GIVEN
    coupon: Coupon = coupons_factory[0]
    transaction_id = "123"
    assert coupon.max_usage == 1

    raw = await db_session.execute(
        select(UsageHistory).where(UsageHistory.coupon_id == coupon.coupon_id)
    )
    usage_histories = raw.scalars()
    assert len(usage_histories.all()) == 0

    # WHEN
    response1 = await async_client.put(
        f"/v2/coupons/reserved",
        json={
            "code": coupon.code,
            "transaction_id": transaction_id,
            "customer_key": "123",
            "purchase_amount": 10,
            "first_purchase": True,
        },
    )

    # THEN
    assert response1.status_code == status.HTTP_204_NO_CONTENT

    # WHEN
    response2 = await async_client.put(
        f"/v2/coupons/confirmed",
        json={"code": coupon.code, "transaction_id": transaction_id},
    )

    # THEN
    assert response2.status_code == status.HTTP_204_NO_CONTENT

    raw = await db_session.execute(
        select(Coupon)
        .options(selectinload(Coupon.usage_histories))
        .where(Coupon.coupon_id == coupon.coupon_id)
    )

    coupon_model: Coupon = raw.scalar_one()
    await db_session.refresh(coupon_model)
    assert coupon_model.confirmed_usage == 1
    assert coupon_model.reserved_usage == 0
    assert coupon_model.total_usage == 1
