from datetime import datetime

import pytest
from fastapi import status
from httpx import AsyncClient
from sqlalchemy import select

from app.models.coupon import Coupon

VALID_DATE_ISOFORMAT = datetime.now().isoformat()


@pytest.mark.asyncio
async def test_should_activate_coupon(
    async_client: AsyncClient, coupons_activation_factory
):
    # GIVEN
    payload = coupons_activation_factory[0]
    # WHEN
    coupon_id = payload.coupon_id

    assert payload.active == False

    response = await async_client.post(f"/v1/coupons/{coupon_id}/activate")

    active_coupon = await async_client.get(f"/v1/coupons/{coupon_id}")
    result = active_coupon.json()

    # THEN
    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert result["active"] == True


@pytest.mark.asyncio
async def test_should_deactivate_coupon(
    async_client: AsyncClient, coupons_activation_factory
):
    # GIVEN
    payload = coupons_activation_factory[1]
    # WHEN
    coupon_id = payload.coupon_id

    assert payload.active == True

    response = await async_client.post(f"/v1/coupons/{coupon_id}/deactivate")

    active_coupon = await async_client.get(f"/v1/coupons/{coupon_id}")
    result = active_coupon.json()

    # THEN
    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert result["active"] == False


@pytest.mark.asyncio
async def test_should_not_activate_inexistent_coupon(
    async_client: AsyncClient, db_session
):
    # GIVEN
    wrong_coupon_id = "WRONG_ID"
    # WHEN

    raw = await db_session.execute(
        select(Coupon).where(Coupon.coupon_id == wrong_coupon_id)
    )
    coupon_model = raw.scalar_one_or_none()
    assert coupon_model is None

    response = await async_client.post(
        f"/v1/coupons/{wrong_coupon_id}/activate"
    )

    # THEN
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_should_not_activate_coupon_that_should_not_be_updated(
    async_client: AsyncClient, coupons_activation_factory
):
    # GIVEN
    payload = coupons_activation_factory[1]
    # WHEN
    coupon_id = payload.coupon_id

    assert payload.active == True

    response = await async_client.post(f"/v1/coupons/{coupon_id}/activate")

    active_coupon = await async_client.get(f"/v1/coupons/{coupon_id}")
    result = active_coupon.json()

    # THEN
    assert response.status_code == status.HTTP_409_CONFLICT
    assert result["active"] == True


@pytest.mark.asyncio
async def test_should_not_deactivate_coupon_that_should_not_be_updated(
    async_client: AsyncClient, coupons_activation_factory
):
    # GIVEN
    payload = coupons_activation_factory[0]
    # WHEN
    coupon_id = payload.coupon_id

    assert payload.active == False

    response = await async_client.post(f"/v1/coupons/{coupon_id}/deactivate")

    active_coupon = await async_client.get(f"/v1/coupons/{coupon_id}")
    result = active_coupon.json()

    # THEN
    assert response.status_code == status.HTTP_409_CONFLICT
    assert result["active"] == False
