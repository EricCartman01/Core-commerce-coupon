from datetime import datetime, timedelta, timezone

import pytest
import pytz
from fastapi import status
from httpx import AsyncClient
from sqlalchemy.sql.expression import select

from app.models.coupon import Coupon
from app.settings import settings
from tests.conftest import date_fix

utc = pytz.utc

VALID_DATE_ISOFORMAT = datetime.now(timezone.utc).isoformat()


@pytest.mark.asyncio
async def test_should_update_coupon_by_id(
    async_client: AsyncClient,
    coupons_factory,
    db_session,
):
    # GIVEN
    coupon = coupons_factory[0]
    assert coupon.active
    assert coupon.description == "coupon 1"
    assert coupon.code == "COUPON1"

    # WHEN
    response = await async_client.put(
        f"/v1/coupons/{coupon.coupon_id}",
        json={
            "description": "coupon X",
            "code": "couponX",
            "customer_key": coupon.customer_key,
            "max_usage": coupon.max_usage,
            "type": coupon.type,
            "value": str(coupon.value),
            "active": coupon.active,
            "valid_from": coupon.valid_from.isoformat(),
            "valid_until": coupon.valid_until.isoformat(),
            "user_create": coupon.user_create,
        },
    )
    # THEN
    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert response.json() is None
    raw = await db_session.execute(
        select(Coupon).where(Coupon.coupon_id == coupon.coupon_id),
    )
    coupon_model = raw.scalar_one()
    assert coupon_model.active
    assert coupon_model.description == "coupon X"
    assert coupon_model.code == "COUPONX"
    assert coupon_model.active is True

    assert coupon_model.code == "COUPONX"


@pytest.mark.asyncio
async def test_should_update_coupon_by_id_with_invalid_id(
    async_client: AsyncClient,
    coupon_payload,
):
    # GIVEN

    # WHEN
    response = await async_client.put("/v1/coupons/123", json=coupon_payload)

    # THEN
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {
        "error_code": "coupon_not_exists",
        "error_message": "coupon not found",
    }


@pytest.mark.asyncio
async def test_should_not_update_coupon_by_id_with_invalid_max_usage(
    async_client: AsyncClient,
    coupons_factory,
):
    # GIVEN
    coupon = coupons_factory[0]
    error_message = "ensure this value is greater than 0"
    assert coupon.max_usage == 1

    # WHEN
    response = await async_client.put(
        f"/v1/coupons/{coupon.coupon_id}",
        json={
            "description": coupon.description,
            "code": coupon.code,
            "customer_key": coupon.customer_key,
            "max_usage": 0,
            "type": coupon.type,
            "value": str(coupon.value),
            "valid_from": coupon.valid_from.isoformat(),
            "valid_until": coupon.valid_until.isoformat(),
            "active": coupon.active,
            "user_create": coupon.user_create,
        },
    )
    result = response.json()

    # THEN
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert result["error_message"][0]["msg"] == error_message
    assert coupon.max_usage == 1


@pytest.mark.asyncio
async def test_should_not_update_coupon_by_id_with_invalid_value(
    async_client: AsyncClient,
    coupons_factory,
):
    # GIVEN
    coupon = coupons_factory[0]
    error_message = "ensure this value is greater than 0"
    assert coupon.value == 10

    # WHEN
    response = await async_client.put(
        f"/v1/coupons/{coupon.coupon_id}",
        json={
            "description": coupon.description,
            "code": coupon.code,
            "customer_key": coupon.customer_key,
            "max_usage": coupon.max_usage,
            "type": coupon.type,
            "value": -2,
            "valid_from": coupon.valid_from.isoformat(),
            "valid_until": coupon.valid_until.isoformat(),
            "active": coupon.active,
            "user_create": "test",
        },
    )
    result = response.json()

    # THEN
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert result["error_message"][0]["msg"] == error_message
    assert coupon.value == 10


@pytest.mark.asyncio
async def test_should_not_update_multiples_coupons_in_a_same_date_range(
    async_client: AsyncClient,
    coupons_factory,
):
    # GIVEN
    coupon = coupons_factory[0]
    error_message = "coupon name already been taken"
    VALID_FROM_FIRST_COUPON = datetime.now(timezone.utc).isoformat()
    VALID_UNTIL_FIRST_COUPON = (
        datetime.now(timezone.utc) + timedelta(minutes=24)
    ).isoformat()

    VALID_FROM_SECOND_COUPON = (
        datetime.now(timezone.utc) + timedelta(minutes=12)
    ).isoformat()

    VALID_UNTIL_SECOND_COUPON = (
        datetime.now(timezone.utc) + timedelta(minutes=36)
    ).isoformat()

    # WHEN
    await async_client.post(
        "/v1/coupons",
        json={
            "description": "coupon x",
            "code": "COUPONX",
            "customer_key": coupon.customer_key,
            "max_usage": coupon.max_usage,
            "type": coupon.type,
            "value": str(coupon.value),
            "valid_from": VALID_FROM_FIRST_COUPON,
            "valid_until": VALID_UNTIL_FIRST_COUPON,
            "user_create": "test",
            "active": coupon.active,
        },
    )

    second_coupon_response = await async_client.post(
        "/v1/coupons",
        json={
            "description": "coupon y",
            "code": "COUPONY",
            "customer_key": coupon.customer_key,
            "max_usage": coupon.max_usage,
            "type": coupon.type,
            "value": str(coupon.value),
            "user_create": "test",
            "valid_from": VALID_FROM_SECOND_COUPON,
            "valid_until": VALID_UNTIL_SECOND_COUPON,
            "active": coupon.active,
        },
    )

    response = await async_client.put(
        f"/v1/coupons/{second_coupon_response.json()['coupon_id']}",
        json={
            "description": coupon.description,
            "code": "COUPONX",
            "customer_key": coupon.customer_key,
            "max_usage": coupon.max_usage,
            "type": coupon.type,
            "value": str(coupon.value),
            "valid_from": VALID_FROM_SECOND_COUPON,
            "valid_until": VALID_UNTIL_SECOND_COUPON,
            "active": coupon.active,
            "user_create": "test",
        },
    )
    result = response.json()

    # THEN
    assert response.status_code == status.HTTP_409_CONFLICT
    assert result["error_message"] == error_message


@pytest.mark.asyncio
async def test_should_not_update_coupon_with_valid_until_in_past_day(
    async_client: AsyncClient,
    coupons_factory,
):
    # GIVEN
    coupon: Coupon = coupons_factory[0]
    error_message = "valid_until must be greater than today"

    # WHEN
    response = await async_client.put(
        f"/v1/coupons/{coupon.coupon_id}",
        json={
            "description": coupon.description,
            "code": coupon.code,
            "customer_key": coupon.customer_key,
            "max_usage": coupon.max_usage,
            "type": coupon.type,
            "value": str(coupon.value),
            "valid_from": "2021-10-26T00:00:00",
            "valid_until": "2021-10-26T00:00:00",
            "active": coupon.active,
            "user_create": coupon.user_create,
        },
    )
    result = response.json()

    # THEN
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert result["error_message"][0]["msg"] == error_message


@pytest.mark.asyncio
async def test_should_not_update_coupon_with_invalid_valid_until(
    async_client: AsyncClient,
    coupons_factory,
):
    # GIVEN
    coupon: Coupon = coupons_factory[0]
    error_message = "valid_until must be greater than valid_from"

    # WHEN
    response = await async_client.put(
        f"/v1/coupons/{coupon.coupon_id}",
        json={
            "description": coupon.description,
            "code": coupon.code,
            "customer_key": coupon.customer_key,
            "max_usage": coupon.max_usage,
            "type": coupon.type,
            "value": str(coupon.value),
            "valid_from": coupon.valid_until.isoformat(),
            "valid_until": coupon.valid_from.isoformat(),
            "active": coupon.active,
            "user_create": coupon.user_create,
        },
    )
    result = response.json()

    # THEN
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert result["error_message"][0]["msg"] == error_message


@pytest.mark.asyncio
async def test_should_not_update_coupon_with_invalid_date_format(
    async_client: AsyncClient,
    coupons_factory,
):
    # GIVEN
    coupon: Coupon = coupons_factory[0]
    error_message = "invalid datetime format"

    # WHEN
    response = await async_client.put(
        f"/v1/coupons/{coupon.coupon_id}",
        json={
            "description": coupon.description,
            "code": coupon.code,
            "customer_key": coupon.customer_key,
            "max_usage": coupon.max_usage,
            "type": coupon.type,
            "value": str(coupon.value),
            "valid_from": "28/12/2023 13:00",
            "valid_until": coupon.valid_from.isoformat(),
            "active": coupon.active,
            "user_create": coupon.user_create,
        },
    )
    result = response.json()

    # THEN
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert result["error_message"][0]["msg"] == error_message


@pytest.mark.asyncio
async def test_should_update_coupon_with_max_usage_none(
    async_client: AsyncClient,
    coupons_factory,
    db_session,
):
    # GIVEN
    coupon: Coupon = coupons_factory[0]

    # WHEN
    response = await async_client.put(
        f"/v1/coupons/{coupon.coupon_id}",
        json={
            "description": coupon.description,
            "code": coupon.code,
            "customer_key": coupon.customer_key,
            "max_usage": None,
            "type": coupon.type,
            "value": str(coupon.value),
            "valid_from": coupon.valid_from.isoformat(),
            "valid_until": coupon.valid_until.isoformat(),
            "active": coupon.active,
            "user_create": coupon.user_create,
        },
    )

    # THEN
    assert response.status_code == status.HTTP_204_NO_CONTENT
    raw = await db_session.execute(
        select(Coupon).where(Coupon.coupon_id == coupon.coupon_id),
    )
    coupon_model = raw.scalar_one()
    assert coupon_model.max_usage is None


@pytest.mark.asyncio
async def test_should_update_coupon_used_with_max_usage_and_valid_until(
    async_client: AsyncClient,
    coupons_factory,
    db_session,
):
    # GIVEN
    coupon: Coupon = coupons_factory[0]
    coupon.max_usage = 1
    valid_until = datetime.now(timezone.utc)

    await async_client.put(
        f"/v1/coupons/{coupon.code}/reserved",
        json={
            "transaction_id": "abc",
            "customer_key": "123456",
            "purchase_amount": 0,
        },
    )

    # WHEN
    response = await async_client.put(
        f"/v1/coupons/{coupon.coupon_id}",
        json={
            "description": coupon.description,
            "code": coupon.code,
            "customer_key": coupon.customer_key,
            "max_usage": 3,
            "type": coupon.type,
            "value": str(coupon.value),
            "valid_from": date_fix(coupon.valid_from),
            "valid_until": date_fix(valid_until),
            "active": coupon.active,
            "user_create": coupon.user_create,
        },
    )

    # THEN
    assert response.status_code == status.HTTP_204_NO_CONTENT
    raw = await db_session.execute(
        select(Coupon).where(Coupon.coupon_id == coupon.coupon_id),
    )
    coupon_model = raw.scalar_one()
    assert coupon_model.max_usage == 3
    assert coupon_model.valid_until.isoformat() == valid_until.isoformat()


@pytest.mark.asyncio
async def test_should_update_coupon_used_only_with_max_usage_and_valid_until(
    async_client: AsyncClient,
    coupons_factory,
):
    # GIVEN
    coupon: Coupon = coupons_factory[0]
    coupon.max_usage = 1
    valid_until = datetime.now(timezone.utc)
    new_description = "New description"

    # WHEN
    await async_client.put(
        f"/v1/coupons/{coupon.code}/reserved",
        json={
            "transaction_id": "abcd",
            "customer_key": "123456",
            "purchase_amount": 10,
            "first_purchase": True,
        },
    )

    response = await async_client.put(
        f"/v1/coupons/{coupon.coupon_id}",
        json={
            "description": new_description,
            "code": coupon.code,
            "customer_key": coupon.customer_key,
            "max_usage": 3,
            "type": coupon.type,
            "value": str(coupon.value),
            "valid_from": date_fix(coupon.valid_from),
            "valid_until": date_fix(valid_until),
            "active": coupon.active,
            "user_create": coupon.user_create,
        },
    )

    # THEN
    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert coupon.max_usage == 3
    assert coupon.valid_until.isoformat() == valid_until.isoformat()
    assert coupon.description != new_description


@pytest.mark.asyncio
async def test_should_not_update_coupon_with_max_usage_less_than_coupon_usage(
    async_client: AsyncClient,
    coupons_factory,
):
    # GIVEN
    coupon: Coupon = coupons_factory[0]
    coupon.max_usage = 1
    valid_until = datetime.now(timezone.utc)

    # WHEN
    response1 = await async_client.put(
        f"/v1/coupons/{coupon.code}/reserved",
        json={
            "transaction_id": "abc",
            "customer_key": "123456",
            "purchase_amount": 10,
            "first_purchase": True,
        },
    )
    await async_client.put(
        f"/v1/coupons/{coupon.code}/reserved",
        json={
            "transaction_id": "abcd",
            "customer_key": "123456",
            "purchase_amount": 10,
            "first_purchase": True,
        },
    )

    response2 = await async_client.put(
        f"/v1/coupons/{coupon.coupon_id}",
        json={
            "description": coupon.description,
            "code": coupon.code,
            "customer_key": coupon.customer_key,
            "max_usage": 1,
            "type": coupon.type,
            "value": str(coupon.value),
            "valid_from": date_fix(coupon.valid_from),
            "valid_until": date_fix(valid_until),
            "active": coupon.active,
            "user_create": coupon.user_create,
        },
    )

    # THEN
    assert response1.status_code == status.HTTP_204_NO_CONTENT
    assert response2.status_code == status.HTTP_412_PRECONDITION_FAILED

    assert coupon.max_usage == 1


@pytest.mark.asyncio
async def test_should_update_coupon_used_with_max_usage_none(
    async_client: AsyncClient,
    coupons_factory,
):
    # GIVEN
    coupon: Coupon = coupons_factory[0]
    coupon.max_usage = 1
    valid_until = datetime.now(timezone.utc)

    await async_client.put(
        f"/v1/coupons/{coupon.code}/reserved",
        json={
            "transaction_id": "abc",
            "customer_key": "123456",
            "purchase_amount": 0,
        },
    )

    # WHEN
    response = await async_client.put(
        f"/v1/coupons/{coupon.coupon_id}",
        json={
            "description": coupon.description,
            "code": coupon.code,
            "customer_key": coupon.customer_key,
            "max_usage": None,
            "type": coupon.type,
            "value": str(coupon.value),
            "valid_from": date_fix(coupon.valid_from),
            "valid_until": date_fix(valid_until),
            "active": coupon.active,
            "user_create": coupon.user_create,
        },
    )

    # THEN
    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert coupon.max_usage is None


@pytest.mark.asyncio
async def test_should_not_update_coupon_with_ok_max_usage_invalid_valid_until(
    async_client: AsyncClient,
    coupons_factory,
):
    # GIVEN
    coupon: Coupon = coupons_factory[0]
    coupon.max_usage = 1
    valid_until = "23/11/2021"

    await async_client.put(
        f"/v1/coupons/{coupon.code}/reserved",
        json={
            "transaction_id": "abc",
            "customer_key": "123456",
            "purchase_amount": 0,
        },
    )

    # WHEN
    response = await async_client.put(
        f"/v1/coupons/{coupon.coupon_id}",
        json={
            "description": coupon.description,
            "code": coupon.code,
            "customer_key": coupon.customer_key,
            "max_usage": 1,
            "type": coupon.type,
            "value": str(coupon.value),
            "valid_from": date_fix(coupon.valid_from),
            "valid_until": valid_until,
            "active": coupon.active,
            "user_create": coupon.user_create,
        },
    )

    # THEN
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.asyncio
async def test_should_update_coupon_with_valid_until_and_unchaged_valid_from(
    async_client: AsyncClient,
    coupons_factory,
):
    # GIVEN
    coupon: Coupon = coupons_factory[0]
    valid_from = datetime(2021, 11, 25).astimezone(utc)
    coupon.valid_from = valid_from
    valid_until = datetime.now(timezone.utc) + timedelta(days=3)

    # WHEN
    response = await async_client.put(
        f"/v1/coupons/{coupon.coupon_id}",
        json={
            "description": coupon.description,
            "code": coupon.code,
            "customer_key": coupon.customer_key,
            "max_usage": coupon.max_usage,
            "type": coupon.type,
            "value": str(coupon.value),
            "valid_from": date_fix(valid_from),
            "valid_until": date_fix(valid_until),
            "active": coupon.active,
            "user_create": coupon.user_create,
        },
    )

    # THEN
    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert coupon.valid_from.isoformat() == valid_from.isoformat()
    assert coupon.valid_until.isoformat() == valid_until.isoformat()


@pytest.mark.asyncio
async def test_should_update_coupon_with_future_valid_from_and_valid_until(
    async_client: AsyncClient,
    coupons_factory,
):
    # GIVEN
    coupon: Coupon = coupons_factory[0]
    coupon.valid_from = datetime(2021, 11, 25)
    future_valid_from = (
        datetime.now(timezone.utc) + timedelta(days=1)
    ).isoformat()
    valid_until = (datetime.now(timezone.utc) + timedelta(days=3)).isoformat()

    # WHEN
    response = await async_client.put(
        f"/v1/coupons/{coupon.coupon_id}",
        json={
            "description": coupon.description,
            "code": coupon.code,
            "customer_key": coupon.customer_key,
            "max_usage": coupon.max_usage,
            "type": coupon.type,
            "value": str(coupon.value),
            "valid_from": future_valid_from,
            "valid_until": valid_until,
            "active": coupon.active,
            "user_create": coupon.user_create,
        },
    )

    # THEN
    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert coupon.valid_from.isoformat() == future_valid_from
    assert coupon.valid_until.isoformat() == valid_until


@pytest.mark.asyncio
async def test_should_not_update_coupon_with_attribute_valid_from_in_past_day(
    async_client: AsyncClient,
    coupons_factory,
):
    # GIVEN
    coupon: Coupon = coupons_factory[0]
    coupon.valid_from = datetime(2021, 11, 25)
    future_past_valid_from = (
        coupon.valid_from + timedelta(days=1)
    ).isoformat()
    valid_until = (datetime.now(timezone.utc) + timedelta(days=3)).isoformat()

    # WHEN
    response = await async_client.put(
        f"/v1/coupons/{coupon.coupon_id}",
        json={
            "description": coupon.description,
            "code": coupon.code,
            "customer_key": coupon.customer_key,
            "max_usage": coupon.max_usage,
            "type": coupon.type,
            "value": str(coupon.value),
            "valid_from": future_past_valid_from,
            "valid_until": valid_until,
            "active": coupon.active,
            "user_create": coupon.user_create,
        },
    )

    # THEN
    assert response.status_code == status.HTTP_412_PRECONDITION_FAILED


@pytest.mark.asyncio
async def test_should_update_coupon_valid_from_to_a_previous_date_greater_than_now(
    async_client: AsyncClient,
    coupons_factory,
    db_session,
):
    # GIVEN
    coupon = coupons_factory[0]
    coupon.valid_from = coupon.valid_from + timedelta(days=2)
    coupon.valid_until = coupon.valid_until + timedelta(days=3)
    assert coupon.active
    assert coupon.description == "coupon 1"
    assert coupon.code == "COUPON1"
    new_valid_from = (coupon.valid_from + timedelta(days=1)).isoformat()

    # WHEN
    response = await async_client.put(
        f"/v1/coupons/{coupon.coupon_id}",
        json={
            "description": "coupon X",
            "code": "couponX",
            "customer_key": coupon.customer_key,
            "max_usage": coupon.max_usage,
            "type": coupon.type,
            "value": str(coupon.value),
            "active": coupon.active,
            "valid_from": new_valid_from,
            "valid_until": coupon.valid_until.isoformat(),
            "user_create": coupon.user_create,
        },
    )
    # THEN
    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert response.json() is None
    raw = await db_session.execute(
        select(Coupon).where(Coupon.coupon_id == coupon.coupon_id),
    )
    coupon_model = raw.scalar_one()
    assert coupon_model.active
    assert coupon_model.description == "coupon X"
    assert coupon_model.code == "COUPONX"
    assert coupon_model.active is True

    assert coupon_model.code == "COUPONX"
    assert coupon_model.valid_from.isoformat() == new_valid_from


@pytest.mark.asyncio
async def test_should_update_limit_per_customer_from_coupon(
    async_client: AsyncClient,
    coupon_payload,
    db_session,
):
    # GIVEN
    coupon = coupon_payload
    coupon["limit_per_customer"] = 2

    assert coupon["limit_per_customer"] == 2

    create_response = await async_client.post("/v1/coupons", json=coupon)

    coupon_create_response = create_response.json()
    # WHEN
    response = await async_client.put(
        f"/v1/coupons/{coupon_create_response['coupon_id']}",
        json={
            "description": coupon_create_response["description"],
            "code": coupon_create_response["code"],
            "customer_key": coupon_create_response["customer_key"],
            "max_usage": coupon_create_response["max_usage"],
            "type": coupon_create_response["type"],
            "value": coupon_create_response["value"],
            "active": coupon_create_response["active"],
            "valid_from": coupon["valid_from"],
            "valid_until": coupon["valid_until"],
            "user_create": coupon_create_response["user_create"],
            "limit_per_customer": 5,
        },
    )
    # THEN
    assert response.status_code == status.HTTP_204_NO_CONTENT
    raw = await db_session.execute(
        select(Coupon).where(
            Coupon.coupon_id == coupon_create_response["coupon_id"]
        ),
    )
    coupon_model = raw.scalar_one()
    assert coupon_model.limit_per_customer == 5


@pytest.mark.asyncio
async def test_should_not_update_limit_per_customer_smaller_than_0(
    async_client: AsyncClient,
    coupon_payload,
    db_session,
):
    # GIVEN
    coupon = coupon_payload
    coupon["limit_per_customer"] = 2
    error_message = "ensure this value is greater than 0"

    assert coupon["limit_per_customer"] == 2

    create_response = await async_client.post(
        "/v1/coupons",
        json=coupon,
    )

    coupon_create_response = create_response.json()
    # WHEN
    response = await async_client.put(
        f"/v1/coupons/{coupon_create_response['coupon_id']}",
        json={
            "description": coupon_create_response["description"],
            "code": coupon_create_response["code"],
            "customer_key": coupon_create_response["customer_key"],
            "max_usage": coupon_create_response["max_usage"],
            "type": coupon_create_response["type"],
            "value": coupon_create_response["value"],
            "active": coupon_create_response["active"],
            "valid_from": coupon["valid_from"],
            "valid_until": coupon["valid_until"],
            "user_create": coupon_create_response["user_create"],
            "limit_per_customer": -1,
        },
    )
    result = response.json()

    # THEN
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert result["error_message"][0]["msg"] == error_message


@pytest.mark.asyncio
async def test_should_not_update_budget_with_usage(
    async_client: AsyncClient,
    coupons_factory,
):
    # GIVEN
    coupon: Coupon = coupons_factory[9]
    valid_until = datetime.now(timezone.utc)

    await async_client.put(
        f"/v1/coupons/{coupon.code}/reserved",
        json={
            "transaction_id": "abc",
            "customer_key": "123456",
            "purchase_amount": 0,
            "first_purchase": True,
        },
    )

    # WHEN
    await async_client.put(
        f"/v1/coupons/{coupon.coupon_id}",
        json={
            "description": coupon.description,
            "code": coupon.code,
            "customer_key": coupon.customer_key,
            "max_usage": None,
            "type": coupon.type,
            "value": 10.00,
            "valid_from": date_fix(coupon.valid_from),
            "valid_until": date_fix(valid_until),
            "active": coupon.active,
            "user_create": coupon.user_create,
            "budget": 15000,
        },
    )

    response = await async_client.get(f"/v1/coupons/{coupon.coupon_id}")
    assert response.json()["budget"] is None


@pytest.mark.asyncio
async def test_should_update_coupon_valid_from_to_a_previous_date_greater_than_now(
    async_client: AsyncClient,
    coupons_factory,
    db_session,
):
    # GIVEN
    coupon = coupons_factory[0]
    coupon.valid_from = coupon.valid_from + timedelta(days=2)
    coupon.valid_until = coupon.valid_until + timedelta(days=3)
    assert coupon.active
    assert coupon.description == "coupon 1"
    assert coupon.code == "COUPON1"
    new_valid_from = (coupon.valid_from + timedelta(days=1)).isoformat()

    # WHEN
    response = await async_client.put(
        f"/v1/coupons/{coupon.coupon_id}",
        json={
            "description": "coupon X",
            "code": "couponX",
            "customer_key": coupon.customer_key,
            "max_usage": coupon.max_usage,
            "type": coupon.type,
            "value": str(coupon.value),
            "active": coupon.active,
            "valid_from": new_valid_from,
            "valid_until": coupon.valid_until.isoformat(),
            "user_create": coupon.user_create,
        },
    )
    # THEN
    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert response.json() is None
    raw = await db_session.execute(
        select(Coupon).where(Coupon.coupon_id == coupon.coupon_id),
    )
    coupon_model = raw.scalar_one()
    assert coupon_model.active
    assert coupon_model.description == "coupon X"
    assert coupon_model.code == "COUPONX"
    assert coupon_model.active is True

    assert coupon_model.code == "COUPONX"
    assert coupon_model.valid_from.isoformat() == new_valid_from


@pytest.mark.asyncio
async def test_should_update_coupon_valid_from_to_a_previous_date_greater_than_now(
    async_client: AsyncClient,
    coupons_factory,
    db_session,
):
    # GIVEN
    coupon = coupons_factory[0]
    coupon.valid_from = coupon.valid_from + timedelta(days=2)
    coupon.valid_until = coupon.valid_until + timedelta(days=3)
    assert coupon.active
    assert coupon.description == "coupon 1"
    assert coupon.code == "COUPON1"
    new_valid_from = (coupon.valid_from + timedelta(days=1)).astimezone(utc)

    # WHEN
    response = await async_client.put(
        f"/v1/coupons/{coupon.coupon_id}",
        json={
            "description": "coupon X",
            "code": "couponX",
            "customer_key": coupon.customer_key,
            "max_usage": coupon.max_usage,
            "type": coupon.type,
            "value": str(coupon.value),
            "active": coupon.active,
            "valid_from": new_valid_from.isoformat(),
            "valid_until": coupon.valid_until.isoformat(),
            "user_create": coupon.user_create,
        },
    )
    # THEN
    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert response.json() is None
    raw = await db_session.execute(
        select(Coupon).where(Coupon.coupon_id == coupon.coupon_id),
    )
    coupon_model = raw.scalar_one()
    assert coupon_model.active
    assert coupon_model.description == "coupon X"
    assert coupon_model.code == "COUPONX"
    assert coupon_model.active is True

    assert coupon_model.code == "COUPONX"
    assert coupon_model.valid_from.isoformat() == new_valid_from.isoformat()


@pytest.mark.asyncio
async def test_should_not_update_limit_per_customer_with_usage(
    async_client: AsyncClient,
    coupons_factory,
):
    # GIVEN
    coupon: Coupon = coupons_factory[9]
    valid_until = datetime.now(timezone.utc)
    assert coupon.limit_per_customer is None

    await async_client.put(
        f"/v1/coupons/{coupon.code}/reserved",
        json={
            "transaction_id": "abc",
            "customer_key": "123456",
            "purchase_amount": 0,
            "first_purchase": True,
        },
    )

    # WHEN
    await async_client.put(
        f"/v1/coupons/{coupon.coupon_id}",
        json={
            "description": coupon.description,
            "code": coupon.code,
            "customer_key": coupon.customer_key,
            "max_usage": None,
            "type": coupon.type,
            "value": 10.00,
            "valid_from": date_fix(coupon.valid_from),
            "valid_until": date_fix(valid_until),
            "active": coupon.active,
            "user_create": coupon.user_create,
            "budget": None,
            "limit_per_customer": 10,
        },
    )

    response = await async_client.get(f"/v1/coupons/{coupon.coupon_id}")
    assert response.json()["limit_per_customer"] is None


@pytest.mark.asyncio
async def test_should_update_valid_from_and_valid_until_in_different_timezones(
    async_client: AsyncClient,
    coupons_factory,
):
    coupon: Coupon = coupons_factory[0]
    tz = timezone(timedelta(hours=-3))
    coupon.valid_from = coupon.valid_from + timedelta(days=1)
    new_valid_from_1 = coupon.valid_from + timedelta(days=1)
    new_valid_until_1 = coupon.valid_until + timedelta(days=3)

    # WHEN
    await async_client.put(
        f"/v1/coupons/{coupon.code}/reserved",
        json={
            "transaction_id": "abcd",
            "customer_key": "123456",
            "purchase_amount": 10,
            "first_purchase": True,
        },
    )

    response1 = await async_client.put(
        f"/v1/coupons/{coupon.coupon_id}",
        json={
            "description": coupon.description,
            "code": coupon.code,
            "customer_key": coupon.customer_key,
            "max_usage": 3,
            "type": coupon.type,
            "value": str(coupon.value),
            "valid_from": new_valid_from_1.astimezone(tz).isoformat(),
            "valid_until": new_valid_until_1.astimezone(tz).isoformat(),
            "active": coupon.active,
            "user_create": coupon.user_create,
        },
    )

    new_valid_from_utc = new_valid_from_1.astimezone(utc)
    new_valid_until_utc = new_valid_until_1.astimezone(utc)

    assert coupon.valid_from.isoformat() == new_valid_from_utc.isoformat()
    assert coupon.valid_until.isoformat() == new_valid_until_utc.isoformat()
    assert response1.status_code == status.HTTP_204_NO_CONTENT

    new_valid_from_2 = (coupon.valid_from + timedelta(days=1)).astimezone(utc)
    new_valid_until_2 = (coupon.valid_until + timedelta(days=3)).astimezone(
        utc
    )

    response2 = await async_client.put(
        f"/v1/coupons/{coupon.coupon_id}",
        json={
            "description": coupon.description,
            "code": coupon.code,
            "customer_key": coupon.customer_key,
            "max_usage": 3,
            "type": coupon.type,
            "value": str(coupon.value),
            "valid_from": new_valid_from_2.isoformat(),
            "valid_until": new_valid_until_2.isoformat(),
            "active": coupon.active,
            "user_create": coupon.user_create,
        },
    )

    assert coupon.valid_from.isoformat() == new_valid_from_2.isoformat()
    assert coupon.valid_until.isoformat() == new_valid_until_2.isoformat()
    assert response2.status_code == status.HTTP_204_NO_CONTENT
