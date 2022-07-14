from asyncio import current_task
from datetime import datetime, timedelta, timezone
from io import StringIO
from typing import AsyncGenerator, Callable

import pytest
import pytz
from fastapi import FastAPI
from httpx import AsyncClient
from sqlalchemy import func
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_scoped_session,
    create_async_engine,
)
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import sessionmaker

from app.api.coupon.v1.schema import CouponInputWithManyCustomers
from app.application import get_app
from app.db.base import Base, CreateCustomID
from app.db.dependencies import get_db_session
from app.models.coupon import Coupon, UsageHistory
from app.models.task import Task
from app.settings import settings


@compiles(CreateCustomID, "sqlite")
def create_custom_id_for_sqlite(element, compiler, **kwargs):
    return compiler.process(func.random())


@pytest.fixture()
async def db_session() -> AsyncSession:
    engine = create_async_engine("sqlite+aiosqlite://", echo=settings.db_echo)
    session_factory = async_scoped_session(
        sessionmaker(
            engine,
            expire_on_commit=False,
            class_=AsyncSession,
        ),
        scopefunc=current_task,
    )
    async with engine.begin() as connection:
        await connection.run_sync(
            Base.metadata.drop_all,
        )  # pylint: disable=E1101
        await connection.run_sync(
            Base.metadata.create_all,
        )  # pylint: disable=E1101
        async with session_factory(bind=connection) as session:
            await session.execute("pragma foreign_keys=ON")
            yield session
            await session.flush()
            await session.rollback()


@pytest.fixture()
def override_get_db(db_session: AsyncSession) -> Callable:
    async def _override_get_db():
        yield db_session

    return _override_get_db


@pytest.fixture()
def app(override_get_db: Callable) -> FastAPI:
    app = get_app()
    app.dependency_overrides[get_db_session] = override_get_db
    return app


@pytest.fixture()
async def async_client(app: FastAPI) -> AsyncGenerator:
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.fixture()
async def coupons_factory(db_session):
    result = []
    valid_from, valid_until = (
        datetime.now(timezone.utc),
        datetime.now(timezone.utc) + timedelta(hours=1),
    )
    coupons = [
        {
            "description": "coupon 1",
            "code": "COUPON1",
            "valid_from": valid_from,
            "valid_until": valid_until,
            "max_usage": 1,
            "type": "percent",
            "value": "10.00",
            "user_create": "Test",
            "create_at": datetime(2021, 10, 26),
        },
        {
            "description": "coupon 2",
            "code": "COUPON2",
            "valid_from": valid_from,
            "valid_until": valid_until,
            "max_usage": 1,
            "type": "percent",
            "value": "10.00",
            "user_create": "Test",
            "create_at": datetime(2021, 10, 26),
        },
        {
            "description": "coupon 3",
            "code": "COUPON3",
            "valid_from": valid_from,
            "valid_until": valid_until,
            "max_usage": 1,
            "type": "percent",
            "value": "10.00",
            "user_create": "Test",
            "create_at": datetime(2021, 10, 26),
        },
        {
            "description": "coupon 4",
            "code": "COUPON4",
            "valid_from": valid_from,
            "valid_until": valid_until,
            "max_usage": 1,
            "type": "percent",
            "value": "10.00",
            "user_create": "Test",
            "create_at": datetime(2021, 10, 26),
        },
        {
            "description": "coupon 5",
            "code": "COUPON5",
            "valid_from": valid_from,
            "valid_until": valid_until,
            "max_usage": 1,
            "type": "percent",
            "value": "10.00",
            "user_create": "Test",
            "create_at": datetime(2021, 10, 26),
        },
        {
            "description": "coupon 6",
            "code": "COUPON6",
            "valid_from": valid_from,
            "valid_until": valid_until,
            "max_usage": 1,
            "type": "percent",
            "value": "10.00",
            "user_create": "Test",
            "create_at": datetime(2021, 10, 26),
        },
        {
            "description": "coupon 7",
            "code": "COUPON7",
            "valid_from": valid_from,
            "valid_until": valid_until,
            "max_usage": 1,
            "type": "percent",
            "value": "10.00",
            "user_create": "Test",
            "create_at": datetime(2021, 10, 26),
        },
        {
            "description": "coupon 8",
            "code": "COUPON8",
            "valid_from": valid_from,
            "valid_until": valid_until,
            "max_usage": 1,
            "type": "percent",
            "value": "10.00",
            "user_create": "Test",
            "create_at": datetime(2021, 10, 26),
        },
        {
            "description": "coupon 9",
            "code": "COUPON9",
            "valid_from": valid_from,
            "valid_until": valid_until,
            "max_usage": 10,
            "type": "percent",
            "value": "10.00",
            "user_create": "Test",
            "create_at": datetime(2021, 10, 26),
        },
        {
            "description": "coupon 10",
            "code": "COUPON10",
            "valid_from": valid_from,
            "valid_until": valid_until,
            "max_usage": 1,
            "type": "percent",
            "value": "10.00",
            "user_create": "Test",
            "create_at": datetime(2021, 10, 26),
        },
    ]
    for coupon in coupons:
        new_coupon = Coupon(**coupon)
        db_session.add(new_coupon)
        await db_session.commit()
        await db_session.refresh(new_coupon)
        result.append(new_coupon)
    return result


@pytest.fixture()
async def coupon_payload():
    valid_from, valid_until = (
        datetime.now(timezone.utc).isoformat(),
        (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat(),
    )
    return {
        "description": "Desconto no Leite Ninho",
        "code": "ninho10",
        "valid_from": valid_from,
        "valid_until": valid_until,
        "max_usage": 1,
        "type": "percent",
        "value": 10,
        "user_create": "test",
    }


@pytest.fixture()
async def coupons_valid_factory(db_session):
    result = []
    valid_from, valid_until = (
        datetime.now(timezone.utc),
        datetime.now(timezone.utc) + timedelta(hours=1),
    )
    coupons = [
        {
            "description": "coupon 1",
            "code": "COUPON1",
            "valid_from": (datetime.now(timezone.utc) + timedelta(hours=1)),
            "valid_until": (datetime.now(timezone.utc) + timedelta(hours=2)),
            "max_usage": 1,
            "type": "percent",
            "value": "10.00",
            "max_amount": None,
            "min_purchase_amount": None,
            "first_purchase": False,
            "user_create": "Test",
            "create_at": datetime(2021, 10, 26),
        },
        {
            "description": "coupon 1",
            "code": "COUPON1",
            "valid_from": (datetime.now(timezone.utc) - timedelta(hours=2)),
            "valid_until": (datetime.now(timezone.utc) - timedelta(hours=1)),
            "max_usage": 1,
            "type": "percent",
            "value": "10.00",
            "max_amount": None,
            "min_purchase_amount": None,
            "first_purchase": False,
            "user_create": "Test",
            "create_at": datetime(2021, 10, 26),
        },
        {
            "description": "coupon 2",
            "code": "COUPON2",
            "valid_from": valid_from,
            "valid_until": valid_until,
            "max_usage": 1,
            "type": "percent",
            "value": "10.00",
            "max_amount": None,
            "min_purchase_amount": 110,
            "first_purchase": True,
            "user_create": "Test",
            "create_at": datetime(2021, 10, 26),
        },
        {
            "description": "coupon 3",
            "code": "COUPON3",
            "customer_key": "USER11",
            "valid_from": valid_from,
            "valid_until": valid_until,
            "max_usage": 1,
            "type": "percent",
            "value": "10.00",
            "max_amount": None,
            "min_purchase_amount": "10.00",
            "first_purchase": True,
            "user_create": "Test",
            "create_at": datetime(2021, 10, 26),
        },
        {
            "description": "coupon 4",
            "code": "COUPON4",
            "customer_key": "USER11",
            "valid_from": valid_from,
            "valid_until": valid_until,
            "max_usage": 1,
            "type": "nominal",
            "value": "10.00",
            "max_amount": None,
            "min_purchase_amount": "10.00",
            "first_purchase": True,
            "user_create": "Test",
            "create_at": datetime(2021, 10, 26),
        },
        {
            "description": "coupon 5",
            "code": "COUPON5",
            "customer_key": "USER11",
            "valid_from": valid_from,
            "valid_until": valid_until,
            "max_usage": 1,
            "type": "percent",
            "value": "20.00",
            "max_amount": 10,
            "min_purchase_amount": "10.00",
            "first_purchase": True,
            "user_create": "Test",
            "create_at": datetime(2021, 10, 26),
        },
        {
            "description": "coupon 6",
            "code": "COUPON6",
            "customer_key": "USER11",
            "valid_from": valid_from,
            "valid_until": valid_until,
            "max_usage": 1,
            "type": "percent",
            "value": "20.00",
            "max_amount": 10,
            "min_purchase_amount": "10.00",
            "first_purchase": False,
            "user_create": "Test",
            "create_at": datetime(2021, 10, 26),
        },
        {
            "description": "coupon 7",
            "code": "COUPON7",
            "customer_key": None,
            "valid_from": valid_from,
            "valid_until": valid_until,
            "max_usage": 1,
            "type": "percent",
            "value": "20.00",
            "max_amount": 10,
            "min_purchase_amount": "10.00",
            "first_purchase": False,
            "user_create": "Test",
            "create_at": datetime(2021, 10, 26),
        },
        {
            "description": "coupon 8",
            "code": "COUPON8",
            "customer_key": None,
            "valid_from": valid_from,
            "valid_until": valid_until,
            "max_usage": 100,
            "type": "percent",
            "value": "20.00",
            "max_amount": 10,
            "min_purchase_amount": "10.00",
            "first_purchase": False,
            "user_create": "Test",
            "create_at": datetime(2021, 10, 26),
        },
        {
            "description": "coupon 9",
            "code": "COUPON9",
            "customer_key": None,
            "valid_from": valid_from,
            "valid_until": valid_until,
            "max_usage": 100,
            "type": "percent",
            "value": "20.00",
            "max_amount": 10,
            "min_purchase_amount": "10.00",
            "first_purchase": False,
            "user_create": "Test",
            "create_at": datetime(2021, 10, 26),
        },
        {
            "description": "coupon 10",
            "code": "COUPON10",
            "customer_key": None,
            "valid_from": valid_from,
            "valid_until": valid_until,
            "max_usage": 100,
            "type": "percent",
            "value": "20.00",
            "max_amount": 10,
            "min_purchase_amount": "10.00",
            "first_purchase": False,
            "user_create": "Test",
            "create_at": datetime(2021, 10, 26),
        },
        {
            "description": "coupon 11",
            "code": "COUPON11",
            "customer_key": None,
            "valid_from": valid_from,
            "valid_until": valid_until,
            "max_usage": 100,
            "type": "percent",
            "value": "20.00",
            "max_amount": 10,
            "min_purchase_amount": "10.00",
            "first_purchase": False,
            "user_create": "Test",
            "create_at": datetime(2021, 10, 26),
        },
        {
            "description": "coupon 12",
            "code": "COUPON12",
            "customer_key": None,
            "valid_from": valid_from,
            "valid_until": valid_until,
            "max_usage": 100,
            "type": "nominal",
            "value": "15.50",
            "max_amount": 0,
            "min_purchase_amount": "10.00",
            "first_purchase": False,
            "user_create": "Test",
            "create_at": datetime(2021, 10, 26),
        },
        {
            "description": "coupon 13",
            "code": "COUPON13",
            "customer_key": None,
            "valid_from": valid_from,
            "valid_until": valid_until,
            "max_usage": 100,
            "type": "nominal",
            "value": "20.00",
            "max_amount": 0,
            "min_purchase_amount": "10.00",
            "first_purchase": False,
            "user_create": "Test",
            "create_at": datetime(2021, 10, 26),
        },
        {
            "description": "coupon 14",
            "code": "COUPON14",
            "customer_key": None,
            "valid_from": valid_from,
            "valid_until": valid_until,
            "max_usage": 100,
            "type": "nominal",
            "value": "20.00",
            "max_amount": 0,
            "min_purchase_amount": None,
            "first_purchase": False,
            "user_create": "Test",
            "create_at": datetime(2021, 10, 26),
        },
        {
            "description": "coupon 15",
            "code": "COUPON15",
            "customer_key": None,
            "valid_from": valid_from,
            "valid_until": valid_until,
            "max_usage": None,
            "type": "nominal",
            "value": "20.00",
            "max_amount": 0,
            "min_purchase_amount": None,
            "first_purchase": False,
            "user_create": "Test",
            "create_at": datetime(2021, 10, 26),
        },
        {
            "description": "coupon 16",
            "code": "COUPON16",
            "customer_key": None,
            "valid_from": valid_from,
            "valid_until": valid_until,
            "max_usage": None,
            "type": "nominal",
            "value": "20.00",
            "max_amount": 0,
            "min_purchase_amount": None,
            "first_purchase": False,
            "user_create": "Test",
            "create_at": datetime(2021, 10, 26),
            "active": True,
        },
    ]
    for coupon in coupons:
        new_coupon = Coupon(**coupon)
        db_session.add(new_coupon)
        await db_session.commit()
        await db_session.refresh(new_coupon)
        result.append(new_coupon)
    return result


@pytest.fixture()
async def coupons_activation_factory(db_session):
    result = []
    valid_from, valid_until = (
        datetime.now(timezone.utc),
        datetime.now(timezone.utc) + timedelta(hours=1),
    )
    coupons = [
        {
            "description": "coupon 1",
            "code": "COUPON1",
            "customer_key": None,
            "valid_from": valid_from,
            "valid_until": valid_until,
            "max_usage": None,
            "type": "nominal",
            "value": 20,
            "max_amount": 0,
            "min_purchase_amount": None,
            "first_purchase": False,
            "user_create": "Test",
            "create_at": datetime(2021, 10, 26),
            "active": False,
        },
        {
            "description": "coupon 2",
            "code": "COUPON2",
            "customer_key": None,
            "valid_from": valid_from,
            "valid_until": valid_until,
            "max_usage": None,
            "type": "nominal",
            "value": 20,
            "max_amount": 0,
            "min_purchase_amount": None,
            "first_purchase": False,
            "user_create": "Test",
            "create_at": datetime(2021, 10, 26),
            "active": True,
        },
    ]
    for coupon in coupons:
        new_coupon = Coupon(**coupon)
        db_session.add(new_coupon)
        await db_session.commit()
        await db_session.refresh(new_coupon)
        result.append(new_coupon)
    return result


@pytest.fixture()
async def coupons_ordered_factory(db_session):
    result = []
    valid_from, valid_until = (
        datetime.now(timezone.utc),
        datetime.now(timezone.utc) + timedelta(hours=1),
    )
    coupons = [
        {
            "description": "order 2",
            "code": "order2",
            "customer_key": None,
            "valid_from": valid_from + timedelta(days=1),
            "valid_until": datetime.now(timezone.utc) + timedelta(days=3),
            "max_usage": None,
            "type": "nominal",
            "value": 20,
            "max_amount": 0,
            "min_purchase_amount": None,
            "first_purchase": False,
            "user_create": "Test",
            "create_at": datetime(2021, 10, 26),
            "active": False,
        },
        {
            "description": "order 1",
            "code": "order1",
            "customer_key": None,
            "valid_from": valid_from + timedelta(days=1),
            "valid_until": datetime.now(timezone.utc) + timedelta(days=2),
            "max_usage": None,
            "type": "nominal",
            "value": 20,
            "max_amount": 0,
            "min_purchase_amount": None,
            "first_purchase": False,
            "user_create": "Test",
            "create_at": datetime(2021, 10, 26),
            "active": True,
        },
    ]
    for coupon in coupons:
        new_coupon = Coupon(**coupon)
        db_session.add(new_coupon)
        await db_session.commit()
        await db_session.refresh(new_coupon)
        result.append(new_coupon)
    return result


@pytest.fixture
async def usage_histories_factory(db_session, coupons_factory):
    usage_histories = [
        {
            "transaction_id": "fake1",
            "customer_key": "customer1",
            "discount_amount": 5000.56,
            "coupon_id": coupons_factory[0].coupon_id,
        },
        {
            "transaction_id": "fake2",
            "customer_key": "customer2",
            "discount_amount": 3000.56,
            "coupon_id": coupons_factory[0].coupon_id,
        },
        {
            "transaction_id": "fake3",
            "customer_key": "customer3",
            "discount_amount": 2000.56,
            "coupon_id": coupons_factory[1].coupon_id,
        },
        {
            "transaction_id": "fake4",
            "customer_key": "customer3",
            "discount_amount": 2000.56,
            "coupon_id": coupons_factory[1].coupon_id,
        },
    ]
    result = []
    for usage_history in usage_histories:
        new_usage_history = UsageHistory(**usage_history)
        db_session.add(new_usage_history)
        await db_session.commit()
        await db_session.refresh(new_usage_history)
        result.append(new_usage_history)
    return result


def date_fix(wrong_date):
    LOCAL_TIMEZONE = pytz.timezone(settings.timezone)
    return (
        wrong_date.replace(tzinfo=pytz.utc)
        .astimezone(LOCAL_TIMEZONE)
        .isoformat()
    )


@pytest.fixture
async def task_factory(db_session):
    tasks = [
        {
            "result": "TEST",
            "data": {"message": "ok"},
        },
    ]
    result = []
    for task in tasks:
        new_task = Task(**task)
        db_session.add(new_task)
        await db_session.commit()
        await db_session.refresh(new_task)
        result.append(new_task)
    return result


@pytest.fixture
def valid_file_with_customers() -> StringIO:
    string_file = StringIO(
        "123\n" "321\n" "test_key\n",
    )
    return string_file


@pytest.fixture
def coupon_with_customer_keys_in_file() -> CouponInputWithManyCustomers:
    valid_from, valid_until = (
        datetime.now(timezone.utc),
        datetime.now(timezone.utc) + timedelta(hours=1),
    )
    schema = CouponInputWithManyCustomers(
        code="test",
        valid_from=valid_from,
        valid_until=valid_until,
        type="nominal",
        value="15.00",
        user_create="user-test",
    )

    return schema
