import csv
import json
from datetime import datetime
from io import StringIO
from tempfile import TemporaryFile
from unittest.mock import Mock, patch

import pytest
from fastapi import status
from httpx import AsyncClient
from sqlalchemy import select

from app.models.coupon import Coupon
from app.models.task import Task

VALID_DATE_ISOFORMAT = datetime.now().isoformat()


@pytest.mark.asyncio
async def test_should_bulk_create_coupon_from_file(
    async_client: AsyncClient,
    db_session,
):
    with patch("app.services.coupon.StorageAWSService") as mocky:
        # GIVEN
        mocky.return_value = Mock(
            upload_file_obj=Mock(return_value="file_key_test"),
        )
        payload = {
            "description": "10% de desconto na cerveja",
            "code": "cerveja10",
            "valid_from": VALID_DATE_ISOFORMAT,
            "valid_until": VALID_DATE_ISOFORMAT,
            "max_usage": 1,
            "type": "percent",
            "value": "10.00",
            "user_create": "test",
            "budget": None,
            "confirmed_usage": 0,
            "first_purchase": False,
            "reserved_usage": 0,
            "total_usage": 0,
        }
        data = [
            ["customerkey1"],
            ["customerkey2"],
            ["customerkey3"],
        ]
        f = StringIO()
        w = csv.writer(f, delimiter=",")

        for row in data:
            w.writerow(row)
        f.seek(0)

        # WHEN
        response = await async_client.post(
            "/v1/coupons/bulk/by-client",
            data=payload,
            files={
                "file_with_customer_keys": (
                    "customer_key.csv",
                    f.getvalue().encode("utf-8"),
                    "text/csv",
                ),
            },
        )
        # THEN
        raw = await db_session.execute(
            select(Coupon).where(
                Coupon.customer_key.in_([c_list[0] for c_list in data]),
            ),
        )
        coupons = raw.scalars().all()

        raw_task = await db_session.execute(select(Task))
        task = raw_task.scalar_one()
        assert response.status_code == status.HTTP_202_ACCEPTED
        assert len(coupons) == 3
        assert json.loads(task.data)["file_key"] == "file_key_test"
        assert mocky.return_value.upload_file_obj.call_count == 1


@pytest.mark.asyncio
async def test_should_bulk_create_coupon_from_customer_keys(
    async_client: AsyncClient,
    db_session,
):
    with patch("app.services.coupon.StorageAWSService") as mocky:
        # GIVEN
        mocky.return_value = Mock(
            upload_file_obj=Mock(return_value="file_key_test"),
        )
        payload = {
            "description": "10% de desconto na cerveja",
            "code": "cerveja10",
            "valid_from": VALID_DATE_ISOFORMAT,
            "valid_until": VALID_DATE_ISOFORMAT,
            "max_usage": 1,
            "type": "percent",
            "value": "10.00",
            "user_create": "test",
            "budget": None,
            "confirmed_usage": 0,
            "first_purchase": False,
            "reserved_usage": 0,
            "total_usage": 0,
            "customer_keys": ["customerkey1", "customerkey2", "customerkey3"],
        }
        # WHEN
        response = await async_client.post(
            "/v1/coupons/bulk/by-client",
            data=payload,
        )

        # THEN
        raw = await db_session.execute(
            select(Coupon).where(
                Coupon.customer_key.in_(payload["customer_keys"]),
            ),
        )
        coupons = raw.scalars().all()
        raw_task = await db_session.execute(select(Task))
        task = raw_task.scalar_one()
        assert response.status_code == status.HTTP_202_ACCEPTED
        assert len(coupons) == 3
        assert (
            json.loads(task.data)["customer_keys"] == payload["customer_keys"]
        )
        assert mocky.return_value.upload_file_obj.call_count == 0


@pytest.mark.asyncio
async def test_should_not_bulk_create_coupon_from_file(
    async_client: AsyncClient,
    db_session,
):
    with patch("app.services.coupon.StorageAWSService") as mocky:
        # GIVEN
        mocky.return_value = Mock(
            upload_file_obj=Mock(return_value="file_key_test"),
        )
        payload = {
            "description": "10% de desconto na cerveja",
            "code": "cerveja10",
            "valid_from": VALID_DATE_ISOFORMAT,
            "valid_until": VALID_DATE_ISOFORMAT,
            "max_usage": 1,
            "type": "nominal",
            "max_amount": "100.00",
            "value": "10.00",
            "user_create": "test",
            "budget": None,
            "confirmed_usage": 0,
            "first_purchase": False,
            "reserved_usage": 0,
            "total_usage": 0,
        }
        data = [
            ["customerkey1"],
            ["customerkey2"],
            ["customerkey3"],
        ]
        f = StringIO()
        w = csv.writer(f, delimiter=",")

        for row in data:
            w.writerow(row)
        f.seek(0)

        # WHEN
        response = await async_client.post(
            "/v1/coupons/bulk/by-client",
            data=payload,
            files={
                "file_with_customer_keys": (
                    "customer_key.csv",
                    f.getvalue().encode("utf-8"),
                    "text/csv",
                ),
            },
        )
        expected_error_message = (
            "Nominal type coupons don't allow max_amount attribute."
        )
        error_message = response.json()["error_message"][0]["msg"]
        # THEN
        raw = await db_session.execute(
            select(Coupon).where(
                Coupon.customer_key.in_([c_list[0] for c_list in data]),
            ),
        )
        coupons = raw.scalars().all()

        raw_task = await db_session.execute(select(Task))
        task = raw_task.scalar_one_or_none()
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert len(coupons) == 0
        assert task is None
        assert expected_error_message == error_message


@pytest.mark.asyncio
async def test_should_ignore_empty_lines_in_file(
    async_client: AsyncClient,
    db_session,
):
    with patch("app.services.coupon.StorageAWSService") as mocky:
        # GIVEN
        mocky.return_value = Mock(
            upload_file_obj=Mock(return_value="file_key_test"),
        )
        payload = {
            "description": "10% de desconto na cerveja",
            "code": "cerveja10",
            "valid_from": VALID_DATE_ISOFORMAT,
            "valid_until": VALID_DATE_ISOFORMAT,
            "max_usage": 1,
            "type": "percent",
            "value": "10.00",
            "user_create": "test",
            "budget": None,
            "confirmed_usage": 0,
            "first_purchase": False,
            "reserved_usage": 0,
            "total_usage": 0,
        }
        data = [
            ["customerkey1"],
            ["     "],
            ["customerkey3"],
            [""],
            ["customerkey5"],
            [""],
            ["customerkey7"],
        ]
        f = StringIO()
        w = csv.writer(f, delimiter=",")

        for row in data:
            w.writerow(row)
        f.seek(0)

        # WHEN
        response = await async_client.post(
            "/v1/coupons/bulk/by-client",
            data=payload,
            files={
                "file_with_customer_keys": (
                    "customer_key.csv",
                    f.getvalue().encode("utf-8"),
                    "text/csv",
                ),
            },
        )
        # THEN
        raw = await db_session.execute(
            select(Coupon).where(
                Coupon.customer_key.in_([c_list[0] for c_list in data]),
            ),
        )
        coupons = raw.scalars().all()
        assert response.status_code == status.HTTP_202_ACCEPTED
        assert len(coupons) == 4


@pytest.mark.asyncio
async def test_should_ignore_empty_index_in_array_customer_keys(
    async_client: AsyncClient,
    db_session,
):
    with patch("app.services.coupon.StorageAWSService") as mocky:
        # GIVEN
        mocky.return_value = Mock(
            upload_file_obj=Mock(return_value="file_key_test"),
        )
        payload = {
            "description": "10% de desconto na cerveja",
            "code": "cerveja10",
            "valid_from": VALID_DATE_ISOFORMAT,
            "valid_until": VALID_DATE_ISOFORMAT,
            "max_usage": 1,
            "type": "percent",
            "value": "10.00",
            "user_create": "test",
            "budget": None,
            "confirmed_usage": 0,
            "first_purchase": False,
            "reserved_usage": 0,
            "total_usage": 0,
            "customer_keys": ["customerkey1", "  ", "", "customerkey4"],
        }
        # WHEN
        response = await async_client.post(
            "/v1/coupons/bulk/by-client",
            data=payload,
        )

        # THEN
        raw = await db_session.execute(
            select(Coupon).where(
                Coupon.customer_key.in_(payload["customer_keys"]),
            ),
        )
        customer_keys_clean = ["customerkey1", "customerkey4"]
        coupons = raw.scalars().all()
        raw_task = await db_session.execute(select(Task))
        task = raw_task.scalar_one()
        assert response.status_code == status.HTTP_202_ACCEPTED
        assert len(coupons) == len(customer_keys_clean)
        assert json.loads(task.data)["customer_keys"] == customer_keys_clean
        assert mocky.return_value.upload_file_obj.call_count == 0


@pytest.mark.asyncio
async def test_should_throw_exception_if_not_csv(
    async_client: AsyncClient,
):
    with patch("app.services.coupon.StorageAWSService") as mocky:
        # GIVEN
        mocky.return_value = Mock(
            upload_file_obj=Mock(return_value="file_key_test"),
        )
        payload = {
            "description": "10% de desconto na cerveja",
            "code": "cerveja10",
            "valid_from": VALID_DATE_ISOFORMAT,
            "valid_until": VALID_DATE_ISOFORMAT,
            "max_usage": 1,
            "type": "percent",
            "value": "10.00",
            "user_create": "test",
            "budget": None,
            "confirmed_usage": 0,
            "first_purchase": False,
            "reserved_usage": 0,
            "total_usage": 0,
        }

        temp = TemporaryFile()
        temp.write(b"teste1")
        temp.seek(0)

        # WHEN
        response = await async_client.post(
            "/v1/coupons/bulk/by-client",
            data=payload,
            files={
                "file_with_customer_keys": temp,
            },
        )
        temp.close()
        result = response.json()
        # THEN
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert (
            result["error_message"][0]["msg"] == "file must be in CSV format"
        )
        assert mocky.return_value.upload_file_obj.call_count == 0
