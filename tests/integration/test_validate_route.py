from datetime import datetime

import pytest
from fastapi import status
from httpx import AsyncClient

VALID_DATE_ISOFORMAT = datetime.now().isoformat()

""""
    ("?code=COUPON10&customer_key=USER10&purchase_amount=100&first_purchase=True"),
"""


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "query_parameters",
    [
        ("?code=COUPON10&customer_key=USER10&purchase_amount=100"),
        ("?code=COUPON10&customer_key=USER10&first_purchase=False"),
        ("?code=COUPON10&purchase_amount=100&first_purchase=True"),
        ("?customer_key=USER10&purchase_amount=100&first_purchase=True"),
        ("?code=COUPON10&customer_key=USER10"),
        ("?code=COUPON10"),
    ],
)
async def test_should_valid_without_required_params(
    async_client: AsyncClient, query_parameters
):
    # GIVEN

    # WHEN
    response = await async_client.get(
        f"/v1/coupons/validate{query_parameters}"
    )

    # THEN
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.asyncio
@pytest.mark.usefixtures("coupons_valid_factory")
async def test_should_invalid_date_for_period_coupon(
    async_client: AsyncClient,
):
    # GIVEN
    query_params = "?code=COUPON1&customer_key=USER10&purchase_amount=100&first_purchase=True"
    # WHEN
    response = await async_client.get(f"/v1/coupons/validate{query_params}")

    # THEN
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
@pytest.mark.usefixtures("coupons_valid_factory")
async def test_should_invalid_coupon_not_in_first_purchase(
    async_client: AsyncClient,
):
    # GIVEN
    query_params = "?code=COUPON2&customer_key=USER10&purchase_amount=100&first_purchase=False"
    # WHEN
    response = await async_client.get(f"/v1/coupons/validate{query_params}")

    # THEN
    assert response.status_code == status.HTTP_412_PRECONDITION_FAILED


@pytest.mark.asyncio
@pytest.mark.usefixtures("coupons_valid_factory")
async def test_should_invalid_coupon_min_amount_greater_than_total_purchase(
    async_client: AsyncClient,
):
    # GIVEN
    query_params = "?code=COUPON2&customer_key=USER10&purchase_amount=100&first_purchase=True"
    # WHEN
    response = await async_client.get(f"/v1/coupons/validate{query_params}")

    # THEN
    assert response.status_code == status.HTTP_412_PRECONDITION_FAILED


@pytest.mark.asyncio
@pytest.mark.usefixtures("coupons_valid_factory")
async def test_should_invalid_customer_key_for_coupon(
    async_client: AsyncClient,
):
    # GIVEN
    query_params = "?code=COUPON3&customer_key=USER10&purchase_amount=100&first_purchase=True"
    # WHEN
    response = await async_client.get(f"/v1/coupons/validate{query_params}")

    # THEN
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "query_parameters",
    [
        (
            "?code=COUPON8&customer_key=USER11&purchase_amount=100&first_purchase=True"
        ),
        (
            "?code=COUPON9&customer_key=USER11&purchase_amount=100&first_purchase=True"
        ),
        (
            "?code=COUPON10&customer_key=USER11&purchase_amount=100&first_purchase=True"
        ),
        (
            "?code=COUPON11&customer_key=USER11&purchase_amount=100&first_purchase=True"
        ),
    ],
)
async def test_should_not_validet_coupon_thats_exceeded_max_used(
    async_client: AsyncClient, query_parameters
):
    # GIVEN

    # WHEN
    response = await async_client.get(
        f"/v1/coupons/validate{query_parameters}"
    )

    # THEN
    assert response.status_code == status.HTTP_404_NOT_FOUND


# Success
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "query_parameters,result",
    [
        (
            "?code=COUPON3&customer_key=USER11&purchase_amount=100&first_purchase=True",
            {
                "code": "COUPON3",
                "description": "coupon 3",
                "type": "percent",
                "value": "10.00",
                "purchase_amount_with_discount": "90.00",
            },
        ),
        (
            "?code=COUPON4&customer_key=USER11&purchase_amount=100&first_purchase=True",
            {
                "code": "COUPON4",
                "description": "coupon 4",
                "type": "nominal",
                "value": "10.00",
                "purchase_amount_with_discount": "90.00",
            },
        ),
        (
            "?code=COUPON5&customer_key=USER11&purchase_amount=100&first_purchase=True",
            {
                "code": "COUPON5",
                "description": "coupon 5",
                "type": "percent",
                "value": "20.00",
                "purchase_amount_with_discount": "90.00",
            },
        ),
        (
            "?code=COUPON6&customer_key=USER11&purchase_amount=100&first_purchase=True",
            {
                "code": "COUPON6",
                "description": "coupon 6",
                "type": "percent",
                "value": "20.00",
                "purchase_amount_with_discount": "90.00",
            },
        ),
        (
            "?code=COUPON6&customer_key=USER11&purchase_amount=100&first_purchase=False",
            {
                "code": "COUPON6",
                "description": "coupon 6",
                "type": "percent",
                "value": "20.00",
                "purchase_amount_with_discount": "90.00",
            },
        ),
        (
            "?code=COUPON7&customer_key=USER11&purchase_amount=100&first_purchase=False",
            {
                "code": "COUPON7",
                "description": "coupon 7",
                "type": "percent",
                "value": "20.00",
                "purchase_amount_with_discount": "90.00",
            },
        ),
        (
            "?code=coupon11&customer_key=USER11&purchase_amount=100&first_purchase=False",
            {
                "code": "COUPON11",
                "description": "coupon 11",
                "type": "percent",
                "value": "20.00",
                "purchase_amount_with_discount": "90.00",
            },
        ),
        (
            "?code=coupon12&customer_key=USER11&purchase_amount=100&first_purchase=False",
            {
                "code": "COUPON12",
                "description": "coupon 12",
                "type": "nominal",
                "value": "15.50",
                "purchase_amount_with_discount": "84.50",
            },
        ),
        (
            "?code=coupon13&customer_key=USER11&purchase_amount=11&first_purchase=False",
            {
                "code": "COUPON13",
                "description": "coupon 13",
                "type": "nominal",
                "value": "20.00",
                "purchase_amount_with_discount": "0.00",
            },
        ),
        (
            "?code=coupon13&customer_key=USER11&purchase_amount=10&first_purchase=False",
            {
                "code": "COUPON13",
                "description": "coupon 13",
                "type": "nominal",
                "value": "20.00",
                "purchase_amount_with_discount": "0.00",
            },
        ),
        (
            "?code=coupon14&customer_key=USER11&purchase_amount=100&first_purchase=False",
            {
                "code": "COUPON14",
                "description": "coupon 14",
                "type": "nominal",
                "value": "20.00",
                "purchase_amount_with_discount": "80.00",
            },
        ),
        (
            "?code=coupon15&customer_key=USER11&purchase_amount=100&first_purchase=False",
            {
                "code": "COUPON15",
                "description": "coupon 15",
                "type": "nominal",
                "value": "20.00",
                "purchase_amount_with_discount": "80.00",
            },
        ),
    ],
)
@pytest.mark.usefixtures("coupons_valid_factory")
async def test_should_validate_coupom(
    async_client: AsyncClient, query_parameters, result
):
    # GIVEN
    # WHEN
    response = await async_client.get(
        f"/v1/coupons/validate{query_parameters}"
    )

    # THEN
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == result
