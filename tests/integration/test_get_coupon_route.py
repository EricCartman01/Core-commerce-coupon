import pytest
import pytz
from fastapi import status
from httpx import AsyncClient

from app.models.coupon import Coupon
from tests.conftest import date_fix


@pytest.mark.asyncio
async def test_should_get_empty_coupons(async_client: AsyncClient):
    # GIVEN

    # WHEN
    response = await async_client.get("/v1/coupons")

    # THEN
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"items": [], "page": 1, "size": 50, "total": 0}


@pytest.mark.asyncio
@pytest.mark.usefixtures("coupons_factory")
@pytest.mark.parametrize(
    "query_parameters,result_length",
    [
        ("", 10),
        ("?page=1&size=10", 10),
        ("?page=2&size=8", 2),
        ("?page=1&size=1", 1),
    ],
)
async def test_should_get_coupons_with_filter(
    async_client: AsyncClient,
    query_parameters,
    result_length,
):
    # GIVEN

    # WHEN
    response = await async_client.get(f"/v1/coupons{query_parameters}")

    # THEN
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()["items"]) == result_length


@pytest.mark.asyncio
async def test_should_get_coupon_by_id(
    async_client: AsyncClient,
    coupons_factory,
):
    # GIVEN
    coupon: Coupon = coupons_factory[0]

    # WHEN
    response = await async_client.get(f"/v1/coupons/{coupon.coupon_id}")

    # THEN
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {
        "coupon_id": coupon.coupon_id,
        "description": "coupon 1",
        "code": "COUPON1",
        "valid_from": date_fix(coupon.valid_from),
        "valid_until": date_fix(coupon.valid_until),
        "max_usage": 1,
        "type": "percent",
        "value": "10.00",
        "max_amount": None,
        "min_purchase_amount": None,
        "first_purchase": False,
        "active": True,
        "customer_key": None,
        "limit_per_customer": None,
        "user_create": "Test",
        "budget": None,
        "confirmed_usage": 0,
        "reserved_usage": 0,
        "total_usage": 0,
    }


@pytest.mark.asyncio
@pytest.mark.usefixtures("coupons_factory")
async def test_should_not_get_coupon_by_id_with_invalid_id(
    async_client: AsyncClient,
):
    # GIVEN

    # WHEN
    response = await async_client.get("/v1/coupons/123")

    # THEN
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {
        "error_code": "coupon_not_exists",
        "error_message": "coupon not found",
    }


@pytest.mark.asyncio
async def test_should_get_ordered_list_of_coupons(
    async_client: AsyncClient, coupons_ordered_factory
):
    # GIVEN

    # WHEN
    response = await async_client.get("/v1/coupons")
    result = response.json()

    # THEN
    assert response.status_code == status.HTTP_200_OK
    assert result["items"][0]["code"] == coupons_ordered_factory[1].code
    assert result["items"][1]["code"] == coupons_ordered_factory[0].code


@pytest.mark.asyncio
async def test_should_return_value_with_two_decimal_places_when_get_coupon(
    async_client: AsyncClient,
    coupons_factory,
):
    # GIVEN
    coupon: Coupon = coupons_factory[0]

    # WHEN
    response = await async_client.get(f"/v1/coupons/{coupon.coupon_id}")

    # THEN
    assert response.status_code == status.HTTP_200_OK
    value = response.json()["value"]
    assert value == "10.00"
