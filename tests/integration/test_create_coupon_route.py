from datetime import datetime, timedelta

import pytest
import pytz
from fastapi import status
from freezegun import freeze_time
from httpx import AsyncClient
from pytz import utc
from sqlalchemy import select

from app.models.coupon import Coupon
from tests.conftest import date_fix

date = datetime.now(pytz.utc)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "payload,result",
    [
        (
            {
                "description": "10% de desconto na cerveja",
                "code": "cerveja10",
                "valid_from": date_fix(date),
                "valid_until": date_fix(date),
                "max_usage": 1,
                "type": "percent",
                "value": "10.00",
                "user_create": "test",
                "budget": None,
                "confirmed_usage": 0,
                "reserved_usage": 0,
                "total_usage": 0,
            },
            {
                "description": "10% de desconto na cerveja",
                "code": "CERVEJA10",
                "customer_key": None,
                "valid_from": date_fix(date),
                "valid_until": date_fix(date),
                "max_usage": 1,
                "type": "percent",
                "value": "10.00",
                "max_amount": None,
                "min_purchase_amount": None,
                "first_purchase": False,
                "active": True,
                "limit_per_customer": None,
                "user_create": "test",
                "budget": None,
                "confirmed_usage": 0,
                "reserved_usage": 0,
                "total_usage": 0,
            },
        ),
        (
            {
                "description": "10% de desconto na cerveja",
                "code": "cerveja10",
                "customer_key": "123452345",
                "valid_from": date_fix(date),
                "valid_until": date_fix(date),
                "max_usage": 1,
                "type": "percent",
                "value": "10.00",
                "user_create": "test",
                "budget": None,
                "confirmed_usage": 0,
                "reserved_usage": 0,
                "total_usage": 0,
            },
            {
                "description": "10% de desconto na cerveja",
                "code": "CERVEJA10",
                "customer_key": "123452345",
                "valid_from": date_fix(date),
                "valid_until": date_fix(date),
                "max_usage": 1,
                "type": "percent",
                "value": "10.00",
                "max_amount": None,
                "min_purchase_amount": None,
                "first_purchase": False,
                "active": True,
                "limit_per_customer": None,
                "user_create": "test",
                "budget": None,
                "confirmed_usage": 0,
                "reserved_usage": 0,
                "total_usage": 0,
            },
        ),
        (
            {
                "description": "10% de desconto na cerveja",
                "code": "cerveja100",
                "customer_key": "123452345",
                "valid_from": date_fix(date),
                "valid_until": date_fix(date),
                "max_usage": 1,
                "type": "percent",
                "value": "10.00",
                "user_create": "test",
                "max_amount": "100.00",
                "min_purchase_amount": "10.00",
                "first_purchase": False,
                "budget": None,
                "confirmed_usage": 0,
                "reserved_usage": 0,
                "total_usage": 0,
            },
            {
                "description": "10% de desconto na cerveja",
                "code": "CERVEJA100",
                "customer_key": "123452345",
                "valid_from": date_fix(date),
                "valid_until": date_fix(date),
                "max_usage": 1,
                "type": "percent",
                "value": "10.00",
                "max_amount": "100.00",
                "min_purchase_amount": "10.00",
                "first_purchase": False,
                "active": True,
                "limit_per_customer": None,
                "user_create": "test",
                "budget": None,
                "confirmed_usage": 0,
                "reserved_usage": 0,
                "total_usage": 0,
            },
        ),
        (
            {
                "description": "10% de desconto na cerveja",
                "code": "cerveja100",
                "customer_key": "123452345",
                "valid_from": date_fix(date),
                "valid_until": date_fix(date),
                "max_usage": 1,
                "type": "percent",
                "value": "10.00",
                "user_create": "test",
                "max_amount": "100.00",
                "min_purchase_amount": "10.00",
                "first_purchase": False,
                "budget": None,
                "confirmed_usage": 0,
                "reserved_usage": 0,
                "total_usage": 0,
            },
            {
                "description": "10% de desconto na cerveja",
                "code": "CERVEJA100",
                "customer_key": "123452345",
                "valid_from": date_fix(date),
                "valid_until": date_fix(date),
                "max_usage": 1,
                "type": "percent",
                "value": "10.00",
                "max_amount": "100.00",
                "min_purchase_amount": "10.00",
                "first_purchase": False,
                "active": True,
                "limit_per_customer": None,
                "user_create": "test",
                "budget": None,
                "confirmed_usage": 0,
                "reserved_usage": 0,
                "total_usage": 0,
            },
        ),
        (
            {
                "description": "20% de desconto na cerveja",
                "code": "cerveja20",
                "valid_from": date_fix(date),
                "valid_until": date_fix(date),
                "max_usage": 1,
                "type": "percent",
                "value": "10.00",
                "user_create": "test",
                "min_purchase_amount": "10.00",
                "first_purchase": True,
                "budget": None,
                "confirmed_usage": 0,
                "reserved_usage": 0,
                "total_usage": 0,
            },
            {
                "description": "20% de desconto na cerveja",
                "code": "CERVEJA20",
                "customer_key": None,
                "valid_from": date_fix(date),
                "valid_until": date_fix(date),
                "max_usage": 1,
                "type": "percent",
                "value": "10.00",
                "max_amount": None,
                "min_purchase_amount": "10.00",
                "first_purchase": True,
                "active": True,
                "limit_per_customer": None,
                "user_create": "test",
                "budget": None,
                "confirmed_usage": 0,
                "reserved_usage": 0,
                "total_usage": 0,
            },
        ),
        (
            {
                "description": "20% de desconto na cerveja",
                "code": "cerveja20",
                "valid_from": date_fix(date),
                "valid_until": date_fix(date),
                "max_usage": 1,
                "type": "percent",
                "value": "10.00",
                "user_create": "test",
                "min_purchase_amount": "10.00",
                "limit_per_customer": 5,
                "first_purchase": True,
                "budget": None,
                "confirmed_usage": 0,
                "reserved_usage": 0,
                "total_usage": 0,
            },
            {
                "description": "20% de desconto na cerveja",
                "code": "CERVEJA20",
                "customer_key": None,
                "valid_from": date_fix(date),
                "valid_until": date_fix(date),
                "max_usage": 1,
                "type": "percent",
                "value": "10.00",
                "max_amount": None,
                "min_purchase_amount": "10.00",
                "first_purchase": True,
                "active": True,
                "limit_per_customer": 5,
                "user_create": "test",
                "budget": None,
                "confirmed_usage": 0,
                "reserved_usage": 0,
                "total_usage": 0,
            },
        ),
    ],
)
async def test_should_create_coupon(
    async_client: AsyncClient,
    payload,
    result,
):
    # GIVEN
    # WHEN
    response = await async_client.post("/v1/coupons", json=payload)
    response_json = response.json()
    result["coupon_id"] = response_json["coupon_id"]

    # THEN
    assert response.status_code == status.HTTP_201_CREATED
    assert response_json == result


@pytest.mark.asyncio
async def test_should_create_coupon_without_create_at_in_payload(
    async_client: AsyncClient,
    coupon_payload,
    db_session,
):
    # GIVEN
    payload = coupon_payload

    # WHEN
    response = await async_client.post("/v1/coupons", json=payload)
    result = response.json()

    # THEN
    assert response.status_code == status.HTTP_201_CREATED
    raw = await db_session.execute(
        select(Coupon).where(Coupon.coupon_id == result["coupon_id"]),
    )
    coupon_model = raw.scalar_one()
    assert coupon_model.create_at is not None


@pytest.mark.asyncio
async def test_should_create_coupon_with_create_at_none(
    async_client: AsyncClient,
    coupon_payload,
    db_session,
):
    # GIVEN
    payload = coupon_payload
    payload["created_at"] = None

    # WHEN
    response = await async_client.post("/v1/coupons", json=payload)
    result = response.json()

    # THEN
    assert response.status_code == status.HTTP_201_CREATED
    raw = await db_session.execute(
        select(Coupon).where(Coupon.coupon_id == result["coupon_id"]),
    )
    coupon_model = raw.scalar_one()
    assert coupon_model.create_at is not None


@pytest.mark.asyncio
async def test_should_create_coupon_with_create_at_valid(
    async_client: AsyncClient,
    coupon_payload,
    db_session,
):
    # GIVEN
    payload = coupon_payload
    payload["create_at"] = datetime.now().isoformat()

    # WHEN
    response = await async_client.post("/v1/coupons", json=payload)
    result = response.json()

    # THEN
    assert response.status_code == status.HTTP_201_CREATED
    raw = await db_session.execute(
        select(Coupon).where(Coupon.coupon_id == result["coupon_id"]),
    )
    coupon_model = raw.scalar_one()
    assert coupon_model.create_at.isoformat() != payload["create_at"]


@pytest.mark.asyncio
async def test_should_create_coupon_because_create_at_is_ignored(
    async_client: AsyncClient,
    coupon_payload,
    db_session,
):
    # GIVEN
    payload = coupon_payload
    payload["create_at"] = "datetime.now().isoformat()"

    # WHEN
    response = await async_client.post("/v1/coupons", json=payload)
    result = response.json()

    # THEN
    assert response.status_code == status.HTTP_201_CREATED
    raw = await db_session.execute(
        select(Coupon).where(Coupon.coupon_id == result["coupon_id"]),
    )
    coupon_model = raw.scalar_one()
    assert coupon_model.create_at is not None


@pytest.mark.asyncio
async def test_should_create_coupon_with_max_amount_none(
    async_client: AsyncClient,
    coupon_payload,
):
    # GIVEN
    payload = coupon_payload
    payload["max_amount"] = None

    # WHEN
    response = await async_client.post("/v1/coupons", json=payload)

    # THEN
    assert response.status_code == status.HTTP_201_CREATED


@pytest.mark.asyncio
async def test_should_not_create_coupon_with_invalid_max_amount(
    async_client: AsyncClient,
    coupon_payload,
):
    # GIVEN
    payload = coupon_payload
    payload["max_amount"] = -1
    error_message = "ensure this value is greater than 0"

    # WHEN
    response = await async_client.post("/v1/coupons", json=payload)
    result = response.json()

    # THEN
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert result["error_message"][0]["msg"] == error_message


@pytest.mark.asyncio
async def test_should_create_coupon_with_max_usage_none(
    async_client: AsyncClient,
    coupon_payload,
):
    # GIVEN
    payload = coupon_payload
    payload["max_usage"] = None

    # WHEN
    response = await async_client.post("/v1/coupons", json=payload)

    # THEN
    assert response.status_code == status.HTTP_201_CREATED


@pytest.mark.asyncio
async def test_should_not_create_coupon_with_invalid_max_usage(
    async_client: AsyncClient,
    coupon_payload,
):
    # GIVEN
    payload = coupon_payload
    payload["max_usage"] = -1
    error_message = "ensure this value is greater than 0"

    # WHEN
    response = await async_client.post("/v1/coupons", json=payload)
    result = response.json()

    # THEN
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert result["error_message"][0]["msg"] == error_message


@pytest.mark.asyncio
async def test_should_save_coupon_code_in_uppercase(
    async_client: AsyncClient,
    coupon_payload,
    db_session,
):
    # GIVEN
    payload = coupon_payload
    payload["code"] = "coupon10"

    # WHEN
    response = await async_client.post("/v1/coupons", json=payload)
    result = response.json()

    # THEN
    assert response.status_code == status.HTTP_201_CREATED
    assert result["code"] == "COUPON10"

    raw = await db_session.execute(
        select(Coupon).where(Coupon.coupon_id == result["coupon_id"]),
    )
    coupon_model = raw.scalar_one()
    assert coupon_model.code == "COUPON10"


@pytest.mark.asyncio
async def test_should_save_coupon_code_in_uppercase(
    async_client: AsyncClient,
    coupon_payload,
    db_session,
):
    # GIVEN
    payload = coupon_payload
    payload["code"] = "coupon10"

    # WHEN
    response = await async_client.post("/v1/coupons", json=payload)
    result = response.json()

    # THEN
    assert response.status_code == status.HTTP_201_CREATED
    assert result["code"] == "COUPON10"

    raw = await db_session.execute(
        select(Coupon).where(Coupon.coupon_id == result["coupon_id"]),
    )
    coupon_model = raw.scalar_one()
    assert coupon_model.code == "COUPON10"


@pytest.mark.asyncio
async def test_should_not_create_coupon_with_empty_string(
    async_client: AsyncClient,
    coupon_payload,
):
    # GIVEN
    payload = coupon_payload
    payload["code"] = ""
    error_message = "Code must not be empty."

    # WHEN
    response = await async_client.post("/v1/coupons", json=payload)
    result = response.json()

    # THEN
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert result["error_message"][0]["msg"] == error_message


@pytest.mark.asyncio
async def test_should_not_create_coupon_with_past_valid_dates(
    async_client: AsyncClient,
    coupon_payload,
):
    # GIVEN
    payload = coupon_payload
    payload["valid_from"] = "2021-10-26T00:00:00"
    payload["valid_until"] = "2021-10-26T00:00:00"
    error_message = "valid_from and valid_until must be greater than today"

    # WHEN
    response = await async_client.post("/v1/coupons", json=coupon_payload)
    result = response.json()

    # THEN
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert result["error_message"][0]["msg"] == error_message


@pytest.mark.asyncio
async def test_should_not_create_coupon_with_invalid_valid_until(
    async_client: AsyncClient,
    coupon_payload,
):
    # GIVEN
    payload = coupon_payload
    payload["valid_from"], payload["valid_until"] = (
        payload["valid_until"],
        payload["valid_from"],
    )
    error_message = "valid_until must be greater than valid_from"

    # WHEN
    response = await async_client.post("/v1/coupons", json=payload)
    result = response.json()

    # THEN
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert result["error_message"][0]["msg"] == error_message


@pytest.mark.asyncio
async def test_should_not_create_multiples_coupons_in_a_same_range_date(
    async_client: AsyncClient,
    coupon_payload,
):
    with freeze_time("2020-12-19"):
        coupon_payload["valid_from"] = datetime.now().isoformat()
        coupon_payload["valid_until"] = (
            datetime.now() + timedelta(days=4)
        ).isoformat()
        await async_client.post(
            "/v1/coupons",
            json=coupon_payload,
        )

        coupon_payload["valid_from"] = datetime(2020, 12, 20).isoformat()
        coupon_payload["valid_until"] = datetime(2020, 12, 21).isoformat()
        response = await async_client.post(
            "/v1/coupons",
            json=coupon_payload,
        )

    result = response.json()
    error_message = "coupon name already been taken"

    # THEN
    assert response.status_code == status.HTTP_409_CONFLICT
    assert result["error_message"] == error_message


@pytest.mark.asyncio
async def test_should_not_create_coupon_with_invalid_date_format(
    async_client: AsyncClient,
    coupon_payload,
):
    # GIVEN
    payload = coupon_payload
    payload["valid_from"] = "28/12/2023 13:00"
    error_message = "invalid datetime format"

    # WHEN
    response = await async_client.post("/v1/coupons", json=payload)
    result = response.json()

    # THEN
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert result["error_message"][0]["msg"] == error_message


@pytest.mark.asyncio
async def test_should_not_create_coupon_with_all_data_none(
    async_client: AsyncClient,
):
    # GIVEN
    payload = {
        "description": None,
        "code": None,
        "valid_from": None,
        "valid_until": None,
        "max_usage": None,
        "type": None,
        "value": None,
        "user_create": None,
    }

    # WHEN
    response = await async_client.post("/v1/coupons", json=payload)

    # THEN
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.asyncio
async def test_should_not_create_coupon_with_invalid_character_in_code(
    async_client: AsyncClient,
    coupon_payload,
):
    # GIVEN
    payload = coupon_payload
    payload["code"] = "c$rvej@/ "
    error_message = "Code must be alphanumeric."

    # WHEN
    response = await async_client.post("/v1/coupons", json=payload)
    result = response.json()

    # THEN
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert result["error_message"][0]["msg"] == error_message


@pytest.mark.asyncio
async def test_should_not_create_coupon_value_bigger_than_100_with_percent_type(
    async_client: AsyncClient,
    coupon_payload,
):
    # GIVEN
    payload = coupon_payload
    payload["type"] = "percent"
    payload["value"] = 120
    error_message = "Value must not be bigger than 100 when type is percent."

    # WHEN
    response = await async_client.post("/v1/coupons", json=payload)
    result = response.json()

    # THEN
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert result["error_message"][0]["msg"] == error_message


@pytest.mark.asyncio
async def test_should_not_create_coupon_budget_less_zero(
    async_client: AsyncClient,
    coupon_payload,
):
    # GIVEN
    payload = coupon_payload
    payload["budget"] = -1
    error_message = "ensure this value is greater than or equal to 0"

    # WHEN
    response = await async_client.post("/v1/coupons", json=payload)
    result = response.json()

    # THEN
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert result["error_message"][0]["msg"] == error_message


@pytest.mark.asyncio
async def test_should_not_create_coupon_when_limit_per_customer_is_smaller_than_0(
    async_client: AsyncClient,
    coupon_payload,
):
    # GIVEN
    payload = coupon_payload
    payload["limit_per_customer"] = -1
    error_message = "ensure this value is greater than 0"

    # WHEN
    response = await async_client.post("/v1/coupons", json=payload)
    result = response.json()

    # THEN
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert result["error_message"][0]["msg"] == error_message
