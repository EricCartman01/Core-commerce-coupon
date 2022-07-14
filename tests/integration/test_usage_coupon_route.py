from datetime import datetime, timedelta
from decimal import Decimal

import pytest
from fastapi import status
from httpx import AsyncClient
from sqlalchemy.orm import selectinload
from sqlalchemy.sql.expression import select

from app.enums import UsageHistoryStatus
from app.models.coupon import Coupon, UsageHistory
from tests.conftest import date_fix

VALID_DATE_ISOFORMAT = datetime.now().isoformat()
VALID_UNTIL_DATE_ISOFORMAT = (
    datetime.now() + timedelta(days=1, hours=2)
).isoformat()


@pytest.mark.asyncio
async def test_should_reserve_coupon(
    async_client: AsyncClient, coupons_factory, db_session
):
    # GIVEN
    coupon: Coupon = coupons_factory[8]
    assert coupon.max_usage == 10

    # WHEN
    response = await async_client.put(
        f"/v1/coupons/{coupon.code}/reserved",
        json={
            "transaction_id": "123456",
            "customer_key": "123456",
            "purchase_amount": 0,
            "first_purchase": True,
        },
    )

    # THEN
    assert response.status_code == status.HTTP_204_NO_CONTENT

    raw = await db_session.execute(
        select(Coupon)
        .options(selectinload(Coupon.usage_histories))
        .where(Coupon.coupon_id == coupon.coupon_id)
    )
    coupon_model = raw.scalar_one()
    await db_session.refresh(coupon_model)

    assert coupon_model.reserved_usage == 1


@pytest.mark.asyncio
async def test_should_reserve_coupon_with_code_in_lowercase(
    async_client: AsyncClient, coupons_factory, db_session
):
    # GIVEN
    coupon: Coupon = coupons_factory[8]
    assert coupon.max_usage == 10
    code = coupon.code.lower()

    # WHEN
    response = await async_client.put(
        f"/v1/coupons/{code}/reserved",
        json={
            "transaction_id": "abc",
            "customer_key": "123456",
            "purchase_amount": 0,
            "first_purchase": True,
        },
    )

    # THEN
    assert response.status_code == status.HTTP_204_NO_CONTENT

    raw = await db_session.execute(
        select(Coupon)
        .options(selectinload(Coupon.usage_histories))
        .where(Coupon.coupon_id == coupon.coupon_id)
    )
    coupon_model = raw.scalar_one()
    await db_session.refresh(coupon_model)

    assert coupon_model.reserved_usage == 1


@pytest.mark.asyncio
async def test_should_reserve_coupon_with_max_usage_none(
    async_client: AsyncClient, coupons_factory, db_session
):
    # GIVEN
    coupon: Coupon = coupons_factory[0]
    coupon.max_usage = None

    # WHEN
    response1 = await async_client.put(
        f"/v1/coupons/{coupon.code}/reserved",
        json={
            "transaction_id": "abc",
            "customer_key": "123456",
            "purchase_amount": 0,
            "first_purchase": True,
        },
    )
    response2 = await async_client.put(
        f"/v1/coupons/{coupon.code}/reserved",
        json={
            "transaction_id": "abcd",
            "customer_key": "123456",
            "purchase_amount": 0,
            "first_purchase": False,
        },
    )
    # THEN
    assert response1.status_code == status.HTTP_204_NO_CONTENT
    assert response2.status_code == status.HTTP_204_NO_CONTENT
    assert coupon.max_usage is None

    raw = await db_session.execute(
        select(UsageHistory)
        .where(UsageHistory.coupon_id == coupon.coupon_id)
        .where(UsageHistory.status == UsageHistoryStatus.RESERVED)
    )
    usage_histories = raw.scalars().all()

    assert len(usage_histories) == 2


@pytest.mark.asyncio
async def test_should_not_reserve_coupon_with_max_usage(
    async_client: AsyncClient, coupons_factory, db_session
):
    # GIVEN
    coupon: Coupon = coupons_factory[0]
    assert coupon.max_usage == 1

    # WHEN
    response1 = await async_client.put(
        f"/v1/coupons/{coupon.code}/reserved",
        json={
            "transaction_id": "abc",
            "customer_key": "123456",
            "purchase_amount": 0,
            "first_purchase": True,
        },
    )

    raw = await db_session.execute(
        select(Coupon)
        .options(selectinload(Coupon.usage_histories))
        .where(Coupon.coupon_id == coupon.coupon_id)
    )
    coupon_model = raw.scalar_one()
    await db_session.refresh(coupon_model)

    assert coupon_model.reserved_usage == 1

    response2 = await async_client.put(
        f"/v1/coupons/{coupon.code}/reserved",
        json={
            "transaction_id": "abcd",
            "customer_key": "123456",
            "purchase_amount": 0,
            "first_purchase": False,
        },
    )
    # THEN
    assert response1.status_code == status.HTTP_204_NO_CONTENT
    assert response2.status_code == status.HTTP_412_PRECONDITION_FAILED

    raw = await db_session.execute(
        select(Coupon)
        .options(selectinload(Coupon.usage_histories))
        .where(Coupon.coupon_id == coupon.coupon_id)
    )
    coupon_model = raw.scalar_one()
    await db_session.refresh(coupon_model)

    assert coupon_model.reserved_usage == 1


@pytest.mark.asyncio
async def test_should_not_reserve_coupon_out_of_period(
    async_client: AsyncClient, coupons_factory, db_session
):
    # GIVEN
    coupon: Coupon = coupons_factory[0]
    coupon.valid_from = datetime(2021, 10, 25)
    coupon.valid_until = datetime(2021, 10, 26)

    # WHEN
    response = await async_client.put(
        f"/v1/coupons/{coupon.code}/reserved",
        json={
            "transaction_id": "abc",
            "customer_key": "123456",
            "purchase_amount": 0,
            "first_purchase": True,
        },
    )

    # THEN
    assert response.status_code == status.HTTP_404_NOT_FOUND

    raw = await db_session.execute(
        select(Coupon)
        .options(selectinload(Coupon.usage_histories))
        .where(Coupon.coupon_id == coupon.coupon_id)
    )
    coupon_model = raw.scalar_one()

    assert coupon_model.reserved_usage == 0


@pytest.mark.asyncio
async def test_should_confirme_usage_of_a_valid_coupon(
    async_client: AsyncClient, coupons_factory, db_session
):
    # GIVEN
    coupon: Coupon = coupons_factory[0]
    assert coupon.max_usage == 1

    raw = await db_session.execute(
        select(UsageHistory)
        .where(UsageHistory.coupon_id == coupon.coupon_id)
    )
    usage_histories = raw.scalars()
    assert len(usage_histories.all()) == 0

    # WHEN
    await async_client.put(
        f"/v1/coupons/{coupon.code}/reserved",
        json={
            "transaction_id": "abc",
            "customer_key": "123456",
            "purchase_amount": 0,
            "first_purchase": True,
        },
    )

    raw = await db_session.execute(
        select(UsageHistory)
        .where(UsageHistory.coupon_id == coupon.coupon_id)
        .where(UsageHistory.status == UsageHistoryStatus.RESERVED)
    )
    histories_reserved = raw.scalars()
    assert len(histories_reserved.all()) == 1

    raw = await db_session.execute(
        select(UsageHistory)
        .where(UsageHistory.coupon_id == coupon.coupon_id)
        .where(UsageHistory.status == UsageHistoryStatus.CONFIRMED)
    )
    histories_confirmed = raw.scalars()
    assert len(histories_confirmed.all()) == 0

    response = await async_client.put(
        f"/v1/coupons/{coupon.code}/confirmed",
        json={
            "transaction_id": "abc"
        }
    )

    # THEN
    assert response.status_code == status.HTTP_204_NO_CONTENT

    raw = await db_session.execute(
        select(UsageHistory)
        .where(UsageHistory.coupon_id == coupon.coupon_id)
        .where(UsageHistory.status == UsageHistoryStatus.RESERVED)
    )
    histories_reserved = raw.scalars()
    assert len(histories_reserved.all()) == 0

    raw = await db_session.execute(
        select(UsageHistory)
        .where(UsageHistory.coupon_id == coupon.coupon_id)
        .where(UsageHistory.status == UsageHistoryStatus.CONFIRMED)
    )
    histories_confirmed = raw.scalars()
    assert len(histories_confirmed.all()) == 1


@pytest.mark.asyncio
async def test_should_confirme_usage_of_a_valid_coupon_with_code_in_lowercase(
    async_client: AsyncClient, coupons_factory, db_session
):
    # GIVEN
    coupon: Coupon = coupons_factory[0]

    assert coupon.max_usage == 1
    raw = await db_session.execute(
        select(UsageHistory)
        .where(UsageHistory.coupon_id == coupon.coupon_id)
        .where(UsageHistory.status == UsageHistoryStatus.CONFIRMED)
    )
    histories_confirmed = raw.scalars()
    assert len(histories_confirmed.all()) == 0

    code = coupon.code.lower()

    # WHEN
    await async_client.put(
        f"/v1/coupons/{coupon.code}/reserved",
        json={
            "transaction_id": "abc",
            "customer_key": "123456",
            "purchase_amount": 0,
            "first_purchase": True,
        },
    )

    response = await async_client.put(
        f"/v1/coupons/{code}/confirmed",
        json={
            "transaction_id": "abc"
        }
    )

    # THEN
    assert response.status_code == status.HTTP_204_NO_CONTENT

    raw = await db_session.execute(
        select(UsageHistory)
        .where(UsageHistory.coupon_id == coupon.coupon_id)
        .where(UsageHistory.status == UsageHistoryStatus.CONFIRMED)
    )
    histories_confirmed = raw.scalars()
    assert len(histories_confirmed.all()) == 1


@pytest.mark.asyncio
async def test_should_not_confirme_usage_of_a_coupon_not_reserved(
    async_client: AsyncClient, coupons_factory, db_session
):
    # GIVEN
    coupon: Coupon = coupons_factory[0]
    assert coupon.max_usage == 1

    raw = await db_session.execute(
        select(UsageHistory)
        .where(UsageHistory.coupon_id == coupon.coupon_id)
    )
    histories_reserved = raw.scalars()
    assert len(histories_reserved.all()) == 0

    # WHEN
    response = await async_client.put(
        f"/v1/coupons/{coupon.code}/confirmed",
        json={
            "transaction_id": "abc"
        }
    )

    # THEN
    assert response.status_code == status.HTTP_404_NOT_FOUND
    raw = await db_session.execute(
        select(UsageHistory)
        .where(UsageHistory.coupon_id == coupon.coupon_id)
    )
    histories = raw.scalars()
    assert len(histories.all()) == 0


@pytest.mark.asyncio
async def test_should_confirm_usage_of_a_coupon_out_of_period(
    async_client: AsyncClient, coupons_factory, db_session
):
    # GIVEN
    coupon: Coupon = coupons_factory[1]

    # WHEN
    await async_client.put(
        f"/v1/coupons/{coupon.code}/reserved",
        json={
            "transaction_id": "abc",
            "customer_key": "123456",
            "purchase_amount": 0,
            "first_purchase": True,
        },
    )
    coupon.valid_from = datetime(2021, 10, 27)
    coupon.valid_until = datetime(2021, 10, 29)

    response = await async_client.put(
        f"/v1/coupons/{coupon.code}/confirmed",
        json={
            "transaction_id": "abc"
        }
    )

    # THEN
    assert response.status_code == status.HTTP_204_NO_CONTENT

    raw = await db_session.execute(
        select(UsageHistory)
        .where(UsageHistory.coupon_id == coupon.coupon_id)
        .where(UsageHistory.status == UsageHistoryStatus.CONFIRMED)
    )
    histories_confirmed = raw.scalars()
    assert len(histories_confirmed.all()) == 1


@pytest.mark.asyncio
async def test_should_unreserve_a_valid_coupon(
    async_client: AsyncClient, coupons_factory, db_session
):
    # GIVEN
    coupon: Coupon = coupons_factory[0]
    raw = await db_session.execute(
        select(UsageHistory)
        .where(UsageHistory.coupon_id == coupon.coupon_id)
    )
    histories_confirmed = raw.scalars()
    assert len(histories_confirmed.all()) == 0

    # WHEN
    await async_client.put(
        f"/v1/coupons/{coupon.code}/reserved",
        json={
            "transaction_id": "abc",
            "customer_key": "123456",
            "purchase_amount": 0,
            "first_purchase": True,
        },
    )

    response = await async_client.put(
        f"/v1/coupons/{coupon.code}/unreserved",
        json={
            "transaction_id": "abc"
        }
    )

    # THEN
    assert response.status_code == status.HTTP_204_NO_CONTENT
    raw = await db_session.execute(
        select(UsageHistory)
        .where(UsageHistory.coupon_id == coupon.coupon_id)
        .where(UsageHistory.status == UsageHistoryStatus.CONFIRMED)
    )
    histories_confirmed = raw.scalars()
    assert len(histories_confirmed.all()) == 0


@pytest.mark.asyncio
async def test_should_not_unreserve_a_confirmed_coupon(
    async_client: AsyncClient, coupons_factory, db_session
):
    # GIVEN
    coupon: Coupon = coupons_factory[0]
    raw = await db_session.execute(
        select(UsageHistory)
        .where(UsageHistory.coupon_id == coupon.coupon_id)
    )
    histories_confirmed = raw.scalars()
    assert len(histories_confirmed.all()) == 0

    # WHEN
    await async_client.put(
        f"/v1/coupons/{coupon.code}/reserved",
        json={
            "transaction_id": "abc",
            "customer_key": "123456",
            "purchase_amount": 0,
            "first_purchase": True,
        },
    )

    await async_client.put(
        f"/v1/coupons/{coupon.code}/confirmed",
        json={
            "transaction_id": "abc"
        }
    )

    response = await async_client.put(
        f"/v1/coupons/{coupon.code}/unreserved",
        json={
            "transaction_id": "abc"
        }
    )

    # THEN
    assert response.status_code == status.HTTP_412_PRECONDITION_FAILED
    raw = await db_session.execute(
        select(UsageHistory)
        .where(UsageHistory.coupon_id == coupon.coupon_id)
        .where(UsageHistory.status == UsageHistoryStatus.CONFIRMED)
    )
    histories_confirmed = raw.scalars()
    assert len(histories_confirmed.all()) == 1


@pytest.mark.asyncio
async def test_should_unreserve_a_valid_coupon_with_code_in_lowercase(
    async_client: AsyncClient, coupons_factory, db_session
):
    # GIVEN
    coupon: Coupon = coupons_factory[0]
    code = coupon.code.lower()

    # WHEN
    await async_client.put(
        f"/v1/coupons/{coupon.code}/reserved",
        json={
            "transaction_id": "abc",
            "customer_key": "123456",
            "purchase_amount": 0,
            "first_purchase": True,
        },
    )

    raw = await db_session.execute(
        select(UsageHistory)
        .where(UsageHistory.coupon_id == coupon.coupon_id)
        .where(UsageHistory.status == UsageHistoryStatus.RESERVED)
    )
    histories_confirmed = raw.scalars()
    assert len(histories_confirmed.all()) == 1

    response = await async_client.put(
        f"/v1/coupons/{code}/unreserved",
        json={
            "transaction_id": "abc"
        }
    )

    # THEN
    assert response.status_code == status.HTTP_204_NO_CONTENT
    raw = await db_session.execute(
        select(UsageHistory)
        .where(UsageHistory.coupon_id == coupon.coupon_id)
        .where(UsageHistory.status == UsageHistoryStatus.RESERVED)
    )
    histories_confirmed = raw.scalars()
    assert len(histories_confirmed.all()) == 0


@pytest.mark.asyncio
async def test_should_not_unreserve_a_coupon_without_reserve(
    async_client: AsyncClient, coupons_factory
):
    # GIVEN
    coupon: Coupon = coupons_factory[0]

    # WHEN
    response = await async_client.put(
        f"/v1/coupons/{coupon.code}/unreserved",
        json={
            "transaction_id": "abc"
        }
    )

    # THEN
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_should_not_reserve_exceeded_budget_coupom(
    async_client: AsyncClient, coupons_factory, db_session
):
    # GIVEN
    coupon = coupons_factory[0]
    error_message = "Discount amount exceed the budget limit."

    # WHEN
    created_coupon_response = await async_client.post(
        f"/v1/coupons",
        json={
            "description": "coupon X",
            "code": "couponX",
            "customer_key": coupon.customer_key,
            "max_usage": 5,
            "type": "nominal",
            "value": 200.00,
            "active": coupon.active,
            "valid_from": date_fix(coupon.valid_from),
            "valid_until": date_fix(coupon.valid_until),
            "user_create": coupon.user_create,
            "budget": 300.00,
        },
    )

    assert created_coupon_response.status_code == status.HTTP_201_CREATED

    created_coupon = created_coupon_response.json()
    code = created_coupon["code"]
    coupon_id = created_coupon["coupon_id"]

    first_response = await async_client.put(
        f"/v1/coupons/{code}/reserved",
        json={
            "transaction_id": "123456",
            "customer_key": "123456",
            "purchase_amount": 210.00,
            "first_purchase": True,
        },
    )

    assert first_response.status_code == status.HTTP_204_NO_CONTENT

    raw = await db_session.execute(
        select(Coupon)
        .options(selectinload(Coupon.usage_histories))
        .where(Coupon.coupon_id == coupon_id)
    )
    coupon_model = raw.scalar_one_or_none()

    assert coupon_model is not None

    await db_session.refresh(coupon_model)

    first_accumulated_value = sum(
        [
            usage_history.discount_amount
            for usage_history in coupon_model.usage_histories
        ]
    )

    assert first_accumulated_value == Decimal("200.00")

    second_response = await async_client.put(
        f"/v1/coupons/{code}/reserved",
        json={
            "transaction_id": "123457",
            "customer_key": "123456",
            "purchase_amount": 210.00,
            "first_purchase": False,
        },
    )

    second_result = second_response.json()

    raw = await db_session.execute(
        select(Coupon)
        .options(selectinload(Coupon.usage_histories))
        .where(Coupon.coupon_id == coupon_id)
    )

    coupon_model = raw.scalar_one_or_none()

    assert coupon_model is not None

    await db_session.refresh(coupon_model)

    second_accumulated_value = sum(
        [
            usage_history.discount_amount
            for usage_history in coupon_model.usage_histories
        ]
    )

    # THEN

    assert second_response.status_code == status.HTTP_412_PRECONDITION_FAILED
    assert second_result["error_message"] == error_message
    assert second_accumulated_value == Decimal("200.00")


@pytest.mark.asyncio
async def test_should_reserve_coupon_and_ensure_that_after_any_reserve_the_total_amount_and_usage_history_len_is_correct(
    async_client: AsyncClient, coupons_factory, db_session
):
    # GIVEN
    coupon: Coupon = coupons_factory[8]
    assert coupon.max_usage == 10

    # WHEN
    first_response = await async_client.put(
        f"/v1/coupons/{coupon.code}/reserved",
        json={
            "transaction_id": "123456",
            "customer_key": "123456",
            "purchase_amount": 100,
            "first_purchase": True,
        },
    )

    raw = await db_session.execute(
        select(Coupon)
        .options(selectinload(Coupon.usage_histories))
        .where(Coupon.coupon_id == coupon.coupon_id)
    )

    coupon_model = raw.scalar_one()
    await db_session.refresh(coupon_model)

    accumulated_value = sum(
        [
            usage_history.discount_amount
            for usage_history in coupon_model.usage_histories
        ]
    )

    # THEN
    assert first_response.status_code == status.HTTP_204_NO_CONTENT
    assert len(coupon_model.usage_histories) == 1
    assert accumulated_value == Decimal("10")

    # WHEN
    second_response = await async_client.put(
        f"/v1/coupons/{coupon.code}/reserved",
        json={
            "transaction_id": "123457",
            "customer_key": "123456",
            "purchase_amount": 100,
            "first_purchase": False,
        },
    )

    raw = await db_session.execute(
        select(Coupon)
        .options(selectinload(Coupon.usage_histories))
        .where(Coupon.coupon_id == coupon.coupon_id)
    )

    coupon_model = raw.scalar_one()
    await db_session.refresh(coupon_model)

    accumulated_value = sum(
        [
            usage_history.discount_amount
            for usage_history in coupon_model.usage_histories
        ]
    )
    # THEN
    assert second_response.status_code == status.HTTP_204_NO_CONTENT
    assert len(coupon_model.usage_histories) == 2
    assert accumulated_value == Decimal("20")

    # WHEN
    third_response = await async_client.put(
        f"/v1/coupons/{coupon.code}/reserved",
        json={
            "transaction_id": "123458",
            "customer_key": "123456",
            "purchase_amount": 100,
            "first_purchase": False,
        },
    )

    raw = await db_session.execute(
        select(Coupon)
        .options(selectinload(Coupon.usage_histories))
        .where(Coupon.coupon_id == coupon.coupon_id)
    )

    coupon_model = raw.scalar_one()
    await db_session.refresh(coupon_model)

    accumulated_value = sum(
        [
            usage_history.discount_amount
            for usage_history in coupon_model.usage_histories
        ]
    )

    # THEN
    assert third_response.status_code == status.HTTP_204_NO_CONTENT
    assert len(coupon_model.usage_histories) == 3
    assert accumulated_value == Decimal("30")


@pytest.mark.asyncio
async def test_should_reserve_coupon_with_a_discount_amount_bigger_than_purchase_amount(
    async_client: AsyncClient, coupons_factory, db_session
):
    # GIVEN
    coupon = coupons_factory[0]
    purchase_amount = 100

    # WHEN
    created_coupon_response = await async_client.post(
        f"/v1/coupons",
        json={
            "description": "coupon X",
            "code": "couponX",
            "customer_key": coupon.customer_key,
            "max_usage": 5,
            "type": "nominal",
            "value": 200.00,
            "active": coupon.active,
            "valid_from": date_fix(coupon.valid_from),
            "valid_until": date_fix(coupon.valid_until),
            "user_create": coupon.user_create,
        },
    )

    created_result = created_coupon_response.json()
    code = created_result["code"]
    coupon_id = created_result["coupon_id"]
    reserve_coupon_response = await async_client.put(
        f"/v1/coupons/{code}/reserved",
        json={
            "transaction_id": "abc",
            "customer_key": "123456",
            "purchase_amount": purchase_amount,
            "first_purchase": True,
        },
    )

    raw = await db_session.execute(
        select(UsageHistory)
        .where(UsageHistory.coupon_id == coupon_id)
        .where(UsageHistory.transaction_id == "abc")
    )
    usage_history = raw.scalar_one_or_none()
    assert usage_history is not None
    assert reserve_coupon_response.status_code == status.HTTP_204_NO_CONTENT
    assert usage_history.discount_amount == Decimal(str(purchase_amount))


@pytest.mark.asyncio
async def test_should_not_reserve_coupon_with_exceeded_limit_per_customer(
    async_client: AsyncClient, coupons_factory, db_session
):
    # GIVEN
    coupon: Coupon = coupons_factory[0]
    coupon.max_usage = None
    coupon.limit_per_customer = 1

    # WHEN
    response1 = await async_client.put(
        f"/v1/coupons/{coupon.code}/reserved",
        json={
            "transaction_id": "abc",
            "customer_key": "123456",
            "purchase_amount": 0,
            "first_purchase": True,
        },
    )
    response2 = await async_client.put(
        f"/v1/coupons/{coupon.code}/reserved",
        json={
            "transaction_id": "abcd",
            "customer_key": "123456",
            "purchase_amount": 0,
            "first_purchase": False,
        },
    )
    # THEN
    assert response1.status_code == status.HTTP_204_NO_CONTENT
    assert response2.status_code == status.HTTP_412_PRECONDITION_FAILED
    assert coupon.max_usage is None
    assert coupon.limit_per_customer == 1

    raw = await db_session.execute(
        select(UsageHistory)
        .where(UsageHistory.coupon_id == coupon.coupon_id)
        .where(UsageHistory.status == UsageHistoryStatus.RESERVED)
    )
    usage_histories = raw.scalars().all()

    assert len(usage_histories) == 1


@pytest.mark.asyncio
async def test_should_reserve_coupon_with_limit_per_customer_none(
    async_client: AsyncClient, coupons_factory, db_session
):
    # GIVEN
    coupon: Coupon = coupons_factory[0]
    coupon.max_usage = None
    coupon.limit_per_customer = None

    # WHEN
    response1 = await async_client.put(
        f"/v1/coupons/{coupon.code}/reserved",
        json={
            "transaction_id": "abc",
            "customer_key": "123456",
            "purchase_amount": 0,
            "first_purchase": True,
        },
    )
    response2 = await async_client.put(
        f"/v1/coupons/{coupon.code}/reserved",
        json={
            "transaction_id": "abcd",
            "customer_key": "123456",
            "purchase_amount": 0,
            "first_purchase": False,
        },
    )
    # THEN
    assert response1.status_code == status.HTTP_204_NO_CONTENT
    assert response2.status_code == status.HTTP_204_NO_CONTENT
    assert coupon.max_usage is None
    assert coupon.limit_per_customer == None

    raw = await db_session.execute(
        select(UsageHistory)
        .where(UsageHistory.coupon_id == coupon.coupon_id)
        .where(UsageHistory.status == UsageHistoryStatus.RESERVED)
    )
    usage_histories = raw.scalars().all()

    assert len(usage_histories) == 2


@pytest.mark.asyncio
async def test_should_reserve_coupon_with_total_purchase_greater_or_equals_than_min_purchase_amount(
    async_client: AsyncClient, coupons_factory, db_session
):
    # GIVEN
    coupon: Coupon = coupons_factory[0]

    created_coupon_response = await async_client.post(
        f"/v1/coupons",
        json={
            "description": "coupon X",
            "code": "couponX",
            "customer_key": coupon.customer_key,
            "max_usage": 5,
            "type": "nominal",
            "value": 20.00,
            "min_purchase_amount": 40.00,
            "active": coupon.active,
            "valid_from": date_fix(coupon.valid_from),
            "valid_until": date_fix(coupon.valid_until),
            "user_create": coupon.user_create,
        },
    )

    assert created_coupon_response.status_code == status.HTTP_201_CREATED

    created_coupon_result = created_coupon_response.json()

    # WHEN
    response1 = await async_client.put(
        f"/v1/coupons/{created_coupon_result['code']}/reserved",
        json={
            "transaction_id": "abc",
            "customer_key": "123456",
            "purchase_amount": 50.00,
            "first_purchase": True,
        },
    )

    response2 = await async_client.put(
        f"/v1/coupons/{created_coupon_result['code']}/reserved",
        json={
            "transaction_id": "abcd",
            "customer_key": "123456",
            "purchase_amount": 40.00,
            "first_purchase": True,
        },
    )

    # THEN
    assert response1.status_code == status.HTTP_204_NO_CONTENT
    assert response2.status_code == status.HTTP_204_NO_CONTENT

    raw = await db_session.execute(
        select(UsageHistory)
        .where(UsageHistory.coupon_id == created_coupon_result["coupon_id"])
        .where(UsageHistory.transaction_id == "abc")
    )
    usage_history = raw.scalar_one()

    assert usage_history.discount_amount == Decimal("20.00")

    raw = await db_session.execute(
        select(UsageHistory)
        .where(UsageHistory.coupon_id == created_coupon_result["coupon_id"])
        .where(UsageHistory.transaction_id == "abcd")
    )
    usage_history = raw.scalar_one()

    assert usage_history.discount_amount == Decimal("20.00")


@pytest.mark.asyncio
async def test_should_not_reserve_coupon_with_total_purchase_smaller_than_min_purchase_amount(
    async_client: AsyncClient, coupons_factory, db_session
):
    # GIVEN
    coupon: Coupon = coupons_factory[0]

    created_coupon_response = await async_client.post(
        f"/v1/coupons",
        json={
            "description": "coupon X",
            "code": "couponX",
            "customer_key": coupon.customer_key,
            "max_usage": 5,
            "type": "nominal",
            "value": 20.00,
            "min_purchase_amount": 40.00,
            "active": coupon.active,
            "valid_from": date_fix(coupon.valid_from),
            "valid_until": date_fix(coupon.valid_until),
            "user_create": coupon.user_create,
        },
    )

    assert created_coupon_response.status_code == status.HTTP_201_CREATED

    created_coupon_result = created_coupon_response.json()

    # WHEN
    response = await async_client.put(
        f"/v1/coupons/{created_coupon_result['code']}/reserved",
        json={
            "transaction_id": "abc",
            "customer_key": "123456",
            "purchase_amount": 30.00,
            "first_purchase": True,
        },
    )

    assert response.status_code == status.HTTP_412_PRECONDITION_FAILED

    raw = await db_session.execute(
        select(UsageHistory).where(
            UsageHistory.coupon_id == created_coupon_result["coupon_id"]
        )
    )
    usage_history = raw.scalar_one_or_none()

    assert usage_history is None


@pytest.mark.asyncio
async def test_should_reserve_coupon_with_total_purchase_equals_than_budget(
    async_client: AsyncClient, coupons_factory, db_session
):
    # GIVEN
    coupon: Coupon = coupons_factory[0]

    created_coupon_response = await async_client.post(
        f"/v1/coupons",
        json={
            "description": "coupon X",
            "code": "couponX",
            "customer_key": coupon.customer_key,
            "max_usage": 5,
            "type": "nominal",
            "value": 100.00,
            "budget": 100.00,
            "active": coupon.active,
            "valid_from": date_fix(coupon.valid_from),
            "valid_until": date_fix(coupon.valid_until),
            "user_create": coupon.user_create,
        },
    )

    assert created_coupon_response.status_code == status.HTTP_201_CREATED

    created_coupon_result = created_coupon_response.json()

    # WHEN
    response = await async_client.put(
        f"/v1/coupons/{created_coupon_result['code']}/reserved",
        json={
            "transaction_id": "abc",
            "customer_key": "123456",
            "purchase_amount": 100.00,
            "first_purchase": True,
        },
    )

    assert response.status_code == status.HTTP_204_NO_CONTENT

    raw = await db_session.execute(
        select(UsageHistory).where(
            UsageHistory.coupon_id == created_coupon_result["coupon_id"]
        )
    )
    usage_history = raw.scalar_one_or_none()

    assert usage_history is not None
    assert usage_history.discount_amount == Decimal("100.00")


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "create_payload,reserve_payload",
    [
        (
            {
                "description": "Coupon x",
                "code": "COUPONX",
                "valid_from": VALID_DATE_ISOFORMAT,
                "valid_until": VALID_UNTIL_DATE_ISOFORMAT,
                "type": "percent",
                "value": "10.00",
                "user_create": "test",
                "budget": None,
                "first_purchase": True,
            },
            {
                "transaction_id": "abc",
                "customer_key": "123456",
                "purchase_amount": 30.00,
                "first_purchase": True,
            },
        ),
        (
            {
                "description": "Coupon x",
                "code": "COUPONY",
                "valid_from": VALID_DATE_ISOFORMAT,
                "valid_until": VALID_UNTIL_DATE_ISOFORMAT,
                "type": "percent",
                "value": "10.00",
                "user_create": "test",
                "budget": None,
                "first_purchase": False,
            },
            {
                "transaction_id": "abcd",
                "customer_key": "123456",
                "purchase_amount": 30.00,
                "first_purchase": True,
            },
        ),
        (
            {
                "description": "Coupon x",
                "code": "COUPONZ",
                "valid_from": VALID_DATE_ISOFORMAT,
                "valid_until": VALID_UNTIL_DATE_ISOFORMAT,
                "type": "percent",
                "value": "10.00",
                "user_create": "test",
                "budget": None,
                "first_purchase": False,
            },
            {
                "transaction_id": "abce",
                "customer_key": "123456",
                "purchase_amount": 30.00,
                "first_purchase": False,
            },
        ),
    ],
)
async def test_should_validate_first_purchase_coupons(
    async_client: AsyncClient, create_payload, reserve_payload
):
    # GIVEN

    # WHEN
    create_response = await async_client.post(
        "/v1/coupons", json=create_payload
    )

    assert create_response.status_code == status.HTTP_201_CREATED

    response_json = create_response.json()
    code = response_json["code"]

    reserve_response = await async_client.put(
        f"/v1/coupons/{code}/reserved", json=reserve_payload
    )

    # THEN

    assert reserve_response.status_code == status.HTTP_204_NO_CONTENT


@pytest.mark.asyncio
async def test_should_not_validate_first_purchase_coupons_that_coupon_is_first_purchase_and_user_is_not(
    async_client: AsyncClient, db_session
):
    # GIVEN

    # WHEN

    create_response = await async_client.post(
        "/v1/coupons",
        json={
            "description": "Coupon x",
            "code": "COUPONY",
            "valid_from": VALID_DATE_ISOFORMAT,
            "valid_until": VALID_UNTIL_DATE_ISOFORMAT,
            "type": "percent",
            "value": "10.00",
            "user_create": "test",
            "budget": None,
            "first_purchase": True,
        },
    )

    assert create_response.status_code == status.HTTP_201_CREATED

    response_json = create_response.json()
    code = response_json["code"]
    coupon_id = response_json["coupon_id"]

    reserve_response = await async_client.put(
        f"/v1/coupons/{code}/reserved",
        json={
            "transaction_id": "abcd",
            "customer_key": "123456",
            "purchase_amount": 30.00,
            "first_purchase": False,
        },
    )

    # THEN

    assert reserve_response.status_code == status.HTTP_412_PRECONDITION_FAILED
    raw = await db_session.execute(
        select(UsageHistory).where(UsageHistory.coupon_id == coupon_id)
    )
    usage_history = raw.scalar_one_or_none()

    assert usage_history is None


@pytest.mark.asyncio
async def test_should_not_raise_http_500_error_when_try_reserve_coupon_with_same_transaction_id(
    async_client: AsyncClient, coupons_factory, db_session
):
    # GIVEN
    coupon: Coupon = coupons_factory[8]
    assert coupon.max_usage == 10

    # WHEN
    response1 = await async_client.put(
        f"/v1/coupons/{coupon.code}/reserved",
        json={
            "transaction_id": "123456",
            "customer_key": "123456",
            "purchase_amount": 0,
            "first_purchase": False,
        },
    )

    response2 = await async_client.put(
        f"/v1/coupons/{coupon.code}/reserved",
        json={
            "transaction_id": "123456",
            "customer_key": "123456",
            "purchase_amount": 0,
            "first_purchase": False,
        },
    )
    # THEN
    assert response1.status_code == status.HTTP_204_NO_CONTENT
    assert response2.status_code == status.HTTP_412_PRECONDITION_FAILED
    assert (
        response2.json()["error_message"]
        == "Already exist a reserve with this transaction id."
    )

    raw = await db_session.execute(
        select(Coupon)
        .options(selectinload(Coupon.usage_histories))
        .where(Coupon.coupon_id == coupon.coupon_id)
    )
    coupon_model = raw.scalar_one()
    await db_session.refresh(coupon_model)

    assert coupon_model.reserved_usage == 1
