from datetime import datetime, timezone
from decimal import Decimal

from fastapi import Depends
from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.sql.sqltypes import Boolean

from app.api.helpers.exception import (
    FirstPurchaseException,
    MaxUsageException,
    MinPurchaseAmountException,
)
from app.db.dependencies import get_db_session
from app.models.coupon import Coupon
from app.repository.base import BaseRepository


class CouponRepository(BaseRepository):
    """Class for accessing model table."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, Coupon)
        self.session = session

    async def get_by_id(self, coupon_id: int) -> Coupon:
        """
        Get a Coupon by id.

        :param coupon_id: id of model.

        :return: a Coupon.
        """
        raw = await self.session.execute(
            select(Coupon)
            .options(selectinload(Coupon.usage_histories))
            .where(Coupon.coupon_id == coupon_id),
        )

        return raw.scalar_one()

    async def get_by_code(self, code: str):
        """
        Get a model by code.

        :param code: code of model.

        :return: Coupon object.
        """
        raw = await self.session.execute(
            select(Coupon)
            .options(selectinload(Coupon.usage_histories))
            .where(Coupon.code == code)
            .where(Coupon.active.is_(True)),
        )
        return raw.scalar_one()

    async def get_by_code_and_valid_period(self, code: str):
        """
        Get a model by code and valid_from and valid until.

        :param code: code of model.

        :return: Coupon object.
        """
        raw = await self.session.execute(
            select(Coupon)
            .options(selectinload(Coupon.usage_histories))
            .where(Coupon.code == code)
            .where(Coupon.valid_from <= datetime.today())
            .where(Coupon.valid_until >= datetime.today())
            .where(Coupon.active.is_(True)),
        )
        return raw.scalar_one()

    async def get_valid_coupon(
        self,
        code: str,
        customer_key: str,
        first_purchase: bool,
        purchase_amount: Decimal,
    ) -> Coupon:
        """
        Check if coupon is valid.

        :param code: code of coupon.
        :param customer_key: key of customer.
        :param first_purchase: indicates if is first purchase.
        :param purchase_amount: total purchase amount.

        :return: True if coupon is valid, False otherwise.
        """

        raw = await self.session.execute(
            select(Coupon)
            .options(selectinload(Coupon.usage_histories))
            .where(Coupon.code == code)
            .where(Coupon.valid_from <= datetime.now(timezone.utc))
            .where(Coupon.valid_until >= datetime.now(timezone.utc))
            .where(
                or_(
                    Coupon.customer_key.is_(None),
                    Coupon.customer_key == customer_key,
                ),
            )
            .where(Coupon.active.is_(True)),
        )
        coupon = raw.scalar_one()

        if coupon.first_purchase and not first_purchase:
            raise FirstPurchaseException()

        if coupon.min_purchase_amount and (
            coupon.min_purchase_amount > purchase_amount
        ):
            raise MinPurchaseAmountException()

        if (
            coupon.max_usage
            and coupon.usage_histories
            and len(coupon.usage_histories) >= coupon.max_usage
        ):
            raise MaxUsageException()

        return coupon

    async def check_duplicate_coupon_name(
        self,
        code: str,
        customer_key: str,
        valid_from: datetime,
        valid_until: datetime,
        coupon_id: str = None,
    ) -> Boolean:
        """
        Check if coupon name already taken in a certain date range.

        :param code: code of coupon.
        :param customer_key: key of customer.
        :param valid_from: initial date of a coupon
        :param valid_until: end date of a coupon
        :param coupon_id: id of coupon

        :return: True if coupon name is being used, False otherwise.
        """
        raw = await self.session.execute(
            select(Coupon)
            .where(Coupon.coupon_id != coupon_id)
            .where(Coupon.code == code)
            .where(
                or_(
                    Coupon.customer_key.is_(None),
                    Coupon.customer_key == customer_key,
                ),
            )
            .where(Coupon.active.is_(True))
            .filter(
                or_(
                    and_(
                        Coupon.valid_from <= valid_from,
                        Coupon.valid_until >= valid_from,
                    ),
                    and_(
                        Coupon.valid_from <= valid_until,
                        Coupon.valid_until >= valid_until,
                    ),
                ),
            ),
        )

        if len(raw.all()) > 0:
            return True
        return False

    async def check_valid_delete(self, coupon_id):
        """
        Check this delete is valid.

        :param coupon_id: id of coupon.

        :return: True if delete is valid, False otherwise.
        """

        raw = await self.session.execute(
            select(Coupon)
            .options(selectinload(Coupon.usage_histories))
            .where(Coupon.coupon_id == coupon_id),
        )
        try:
            (result,) = raw.one_or_none()

            return (
                isinstance(result.usage_histories, list)
                and len(result.usage_histories) == 0
            )
        except TypeError:
            return True

    async def activate_coupon(self, coupon_id):
        """
        Activate a coupon.

        :param coupon_id: id of coupon.

        :return: True if cannot activate, False otherwise.
        """

        try:
            raw = await self.session.execute(
                select(Coupon).where(Coupon.coupon_id == coupon_id),
            )
            coupon = raw.scalar_one()
            if coupon.active:
                return True

            await self.update(
                (Coupon.coupon_id == coupon_id),
                {"active": True},
            )

        except AttributeError:
            return True

    async def deactivate_coupon(self, coupon_id):
        """
        Deactivate a coupon.

        :param coupon_id: id of coupon.

        :return: True if cannot deactivate, False otherwise.
        """

        try:
            raw = await self.session.execute(
                select(Coupon).where(Coupon.coupon_id == coupon_id),
            )
            coupon = raw.scalar_one()

            if not coupon.active:
                return True

            await self.update(
                (Coupon.coupon_id == coupon_id),
                {"active": False},
            )

        except AttributeError:
            return True
