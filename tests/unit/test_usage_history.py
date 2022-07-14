from datetime import datetime, timedelta

import pytest
from sqlalchemy import and_, select
from sqlalchemy.exc import IntegrityError

from app.api.helpers.exception import IntegrityException
from app.enums import UsageHistoryStatus
from app.models.coupon import UsageHistory
from app.repository.usage_history import UsageHistoryRepository


@pytest.mark.asyncio
async def test_create_usage_history(coupons_factory, db_session):
    # GIVEN
    usage_history_data = {
        "transaction_id": "fake",
        "customer_key": "customer",
        "discount_amount": 5000.56,
        "coupon_id": coupons_factory[0].coupon_id,
    }

    # WHEN
    usage_history = UsageHistory(**usage_history_data)
    db_session.add(usage_history)
    await db_session.commit()
    await db_session.refresh(usage_history)

    # THEN
    assert usage_history.status in UsageHistoryStatus.RESERVED
    assert isinstance(usage_history.created_at, datetime)


@pytest.mark.asyncio
async def test_not_create_usage_history_with_duplicated_transaction_id(
    coupons_factory, db_session
):
    # GIVEN
    usage_history_data = {
        "transaction_id": "fake",
        "customer_key": "customer",
        "discount_amount": 5000.56,
        "coupon_id": coupons_factory[0].coupon_id,
    }

    # WHEN
    usage_history = UsageHistory(**usage_history_data)
    db_session.add(usage_history)
    await db_session.commit()
    await db_session.refresh(usage_history)

    # THEN
    with pytest.raises(IntegrityError):
        usage_history_copy = UsageHistory(**usage_history_data)
        db_session.add(usage_history_copy)
        await db_session.commit()


@pytest.mark.asyncio
async def test_create_usage_history_with_usage_history_repository(
    coupons_factory, db_session
):
    # GIVEN
    usage_history_data = {
        "transaction_id": "fake",
        "customer_key": "customer",
        "discount_amount": 5000.56,
        "coupon_id": coupons_factory[0].coupon_id,
    }

    # WHEN
    usage_history_obj = UsageHistory(**usage_history_data)
    repository = UsageHistoryRepository(db_session)
    usage_history_model = await repository.create(usage_history_obj)

    # THEN
    assert usage_history_model.status in UsageHistoryStatus.RESERVED
    assert isinstance(usage_history_model.created_at, datetime)


@pytest.mark.asyncio
async def test_should_not_create_usage_history_with_duplicated_transaction_and_coupon_id(
    coupons_factory, db_session
):
    # GIVEN
    usage_history_data_1 = {
        "transaction_id": "fakeawesome",
        "customer_key": "customer",
        "discount_amount": 5000.56,
        "coupon_id": coupons_factory[0].coupon_id,
    }
    usage_history_data_2 = {
        "transaction_id": "fakeawesome",
        "customer_key": "customer",
        "discount_amount": 5000.56,
        "coupon_id": coupons_factory[0].coupon_id,
    }

    # THEN
    with pytest.raises(IntegrityError):
        repository = UsageHistoryRepository(db_session)

        usage_history_obj = UsageHistory(**usage_history_data_1)
        db_session.add(usage_history_obj)
        await db_session.commit()
        await db_session.refresh(usage_history_obj)

        usage_history_obj_2 = UsageHistory(**usage_history_data_2)
        db_session.add(usage_history_obj_2)
        await db_session.commit()
        await db_session.refresh(usage_history_obj_2)


@pytest.mark.asyncio
async def test_delete_usage_history(usage_histories_factory, db_session):
    # GIVEN
    repository = UsageHistoryRepository(db_session)
    usage_history_model = usage_histories_factory[0]

    # WHEN
    assert usage_history_model.status in UsageHistoryStatus.RESERVED
    await repository.delete(usage_history_model.transaction_id)

    # THEN
    raw = await db_session.execute(
        select(UsageHistory).where(
            UsageHistory.transaction_id == usage_history_model.transaction_id
        )
    )
    assert not raw.scalar_one_or_none()


@pytest.mark.asyncio
async def test_get_by_transaction_id_usage_history(
    usage_histories_factory, db_session
):
    # GIVEN
    repository = UsageHistoryRepository(db_session)
    usage_history_created = usage_histories_factory[0]

    # WHEN
    usage_history_model = await repository.get_one(
        usage_history_created.transaction_id, usage_history_created.coupon_id
    )

    # THEN
    assert usage_history_model.id == usage_history_created.id
    assert (
        usage_history_model.transaction_id
        == usage_history_created.transaction_id
    )
    assert (
        usage_history_model.customer_key == usage_history_created.customer_key
    )
    assert usage_history_model.coupon_id == usage_history_created.coupon_id


@pytest.mark.asyncio
async def test_filter_usage_history(usage_histories_factory, db_session):
    # GIVEN
    repository = UsageHistoryRepository(db_session)
    filter_sql = [
        UsageHistory.customer_key == usage_histories_factory[2].customer_key,
        UsageHistory.created_at >= (datetime.today() - timedelta(days=1)),
    ]

    # WHEN
    collection = await repository.get_all(and_(True, *filter_sql))
    result = await collection.fetchall()

    # THEN
    assert len(result) == 2
    assert (
        result[0].transaction_id == usage_histories_factory[2].transaction_id
    )
    assert result[0].customer_key == usage_histories_factory[2].customer_key
    assert (
        result[0].discount_amount == usage_histories_factory[2].discount_amount
    )
    assert result[0].coupon_id == usage_histories_factory[2].coupon_id
    assert (
        result[1].transaction_id == usage_histories_factory[3].transaction_id
    )
    assert result[1].customer_key == usage_histories_factory[3].customer_key
    assert (
        result[1].discount_amount == usage_histories_factory[3].discount_amount
    )
    assert result[1].coupon_id == usage_histories_factory[3].coupon_id


@pytest.mark.asyncio
async def test_update_status_usage_history(
    usage_histories_factory, db_session
):
    # GIVEN
    repository = UsageHistoryRepository(db_session)
    usage_history_created = usage_histories_factory[0]
    assert usage_history_created.status in UsageHistoryStatus.RESERVED

    # WHEN
    row_count = await repository.update_status(
        usage_history_created.transaction_id, UsageHistoryStatus.CONFIRMED
    )
    raw = await db_session.execute(
        select(UsageHistory).where(
            UsageHistory.transaction_id == usage_history_created.transaction_id
        )
    )
    obj = raw.scalar_one()

    # THEN
    assert obj.id == usage_history_created.id
    assert obj.status in UsageHistoryStatus.CONFIRMED
    assert obj.status == "confirmed"
    assert row_count == 1


@pytest.mark.asyncio
async def test_should_create_multiple_usage_history_for_one_transaction(
    coupons_factory, db_session
):
    # GIVEN
    usage_history_data_1 = {
        "transaction_id": "fakeawesome",
        "customer_key": "customer",
        "discount_amount": 5000.56,
        "coupon_id": coupons_factory[0].coupon_id,
    }
    usage_history_data_2 = {
        "transaction_id": "fakeawesome",
        "customer_key": "customer",
        "discount_amount": 5000.56,
        "coupon_id": coupons_factory[1].coupon_id,
    }
    usage_history_data_3 = {
        "transaction_id": "fakeawesome",
        "customer_key": "customer",
        "discount_amount": 5000.56,
        "coupon_id": coupons_factory[2].coupon_id,
    }

    usage_history_obj = UsageHistory(**usage_history_data_1)
    db_session.add(usage_history_obj)
    await db_session.commit()

    usage_history_obj_2 = UsageHistory(**usage_history_data_2)
    db_session.add(usage_history_obj_2)
    await db_session.commit()

    usage_history_obj_3 = UsageHistory(**usage_history_data_3)
    db_session.add(usage_history_obj_3)
    await db_session.commit()


@pytest.mark.asyncio
async def test_should_usage_the_same_coupon_in_multiples_transactions(
    coupons_factory, db_session
):
    # GIVEN
    transactions_ids = ["t1", "t2", "t3", "t4"]
    coupon_id: str = coupons_factory[0].coupon_id

    # THEN
    for transaction_id in transactions_ids:
        usage_history_data_1 = {
            "transaction_id": transaction_id,
            "customer_key": "customer",
            "discount_amount": 5000.56,
            "coupon_id": coupon_id,
        }
        usage_history_obj = UsageHistory(**usage_history_data_1)
        db_session.add(usage_history_obj)
        await db_session.commit()
