from datetime import datetime, timedelta, timezone

import pytest
from fastapi import status
from httpx import AsyncClient
from sqlalchemy.sql.expression import select

from app.enums import UsageHistoryStatus
from app.models.coupon import UsageHistory

VALID_DATE_ISOFORMAT = datetime.now().isoformat()


@pytest.mark.asyncio
async def test_should_delete_coupon(
    async_client: AsyncClient, db_session, coupons_factory
):
    # GIVEN
    coupon = coupons_factory[0]
    assert coupon.active

    # WHEN
    response = await async_client.delete(f"/v1/coupons/{coupon.coupon_id}")
    await db_session.refresh(coupon)

    # THEN
    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert response.json() is None
    assert not coupon.active


@pytest.mark.asyncio
async def test_should_not_delete_coupon_with_invalid_id(
    async_client: AsyncClient,
):
    # GIVEN

    # WHEN
    response = await async_client.delete("/v1/coupons/20")

    # THEN
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {
        "error_code": "coupon_not_exists",
        "error_message": "coupon not found",
    }


@pytest.mark.asyncio
async def test_should_not_delete_an_used_coupon(
    async_client: AsyncClient, coupon_payload, db_session
):

    # GIVEN

    VALID_UNTIL = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
    coupon = coupon_payload
    error_message = "Could not delete an used coupon"

    coupon["valid_until"] = VALID_UNTIL

    # WHEN
    coupon_response = await async_client.post("/v1/coupons", json=coupon)

    coupon_code = coupon_response.json()["code"]
    coupon_id = coupon_response.json()["coupon_id"]

    await async_client.put(
        f"/v1/coupons/{coupon_code}/reserved",
        json={
            "first_purchase": True,
            "transaction_id": "123",
            "customer_key": "string",
            "purchase_amount": 0,
        },
    )

    await async_client.put(
        f"/v1/coupons/{coupon_code}/confirmed",
        json={
            "transaction_id": "123",
        },
    )
    raw = await db_session.execute(
        select(UsageHistory)
        .where(UsageHistory.coupon_id == coupon_id)
        .where(UsageHistory.status == UsageHistoryStatus.CONFIRMED)
    )
    usage_histories = raw.scalars().all()
    assert len(usage_histories) == 1
    await db_session.close()

    response = await async_client.put(
        f"/v1/coupons/{coupon_code}/confirmed",
        json={
            "transaction_id": "123",
        },
    )
    raw = await db_session.execute(
        select(UsageHistory)
        .where(UsageHistory.coupon_id == coupon_id)
        .where(UsageHistory.status == UsageHistoryStatus.CONFIRMED)
    )
    usage_histories = raw.scalars().all()

    assert len(usage_histories) == 1

    delete_response = await async_client.delete(f"/v1/coupons/{coupon_id}")
    result = delete_response.json()

    # THEN
    assert delete_response.status_code == status.HTTP_409_CONFLICT
    assert result["error_message"] == error_message
