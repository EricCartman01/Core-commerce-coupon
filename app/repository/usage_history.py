from fastapi import Depends
from sqlalchemy import and_, delete, join, select
from sqlalchemy.ext.asyncio import AsyncScalarResult, AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.sql.elements import BinaryExpression

from app.db.base import Base
from app.db.dependencies import get_db_session
from app.enums import UsageHistoryStatus
from app.models.coupon import Coupon, UsageHistory
from app.repository.base import BaseRepository


class UsageHistoryRepository(BaseRepository):
    """Class for accessing UsageHistory Model Table"""

    def __init__(self, session: AsyncSession):
        super().__init__(session, UsageHistory)
        self.session = session

    async def get_one(self, transaction_id: str, coupon_id: str) -> Base:
        """
        Get a model by transaction_id.

        :param transaction_id: transaction_id of model.
        :param coupon_id: coupon_id of model.

        :return: a model.
        """
        raw = await self.session.execute(
            select(self.model).where(
                and_(
                    self.model.transaction_id == transaction_id,
                    self.model.coupon_id == coupon_id,
                )
            ),
        )
        return raw.scalar_one()

    async def get_all(
        self, query_filter: BinaryExpression = None
    ) -> AsyncScalarResult:
        """
        Get all models with limit/offset pagination.

        :param query_filter: to filter list os models.

        :return: tuple of streams of model.
        """
        query = select(self.model)
        if query_filter is not None:
            query = query.filter(query_filter)
        raw_stream = await self.session.stream(query)

        return raw_stream.scalars()

    async def update_status(
        self, transaction_id: str, status: UsageHistoryStatus
    ) -> int:
        """
        Update UsageHistory model by transaction_id.

        :param transaction_id: criteria of model to update.
        :param status: new status to update the model.

        :returns: count of rows to updated or -1 if error.

        :raises NoResultFound: 404 - UsageHistory not found
        :raises AssertionError: 404 - UsageHistory not found
        """
        rowcount = await self.update(
            query_filter=and_(
                True, self.model.transaction_id == transaction_id
            ),
            data_to_update={"status": status},
        )

        return rowcount

    async def delete(self, transaction_id: str):
        """
        Delete usage history model in database.

        :param transaction_id: transaction_id of usage history model.
        """
        return await self.session.execute(
            delete(self.model).where(
                self.model.transaction_id == transaction_id
            )
        )

    async def get_by_coupon_id(self, coupon_id: str):
        """
        Get a model by coupon_id.

        :param coupon_id: coupon_id of model.
        return: tuple of streams of model
        """
        raw = await self.session.execute(
            select(self.model).where(self.model.coupon_id == coupon_id),
        )

        return raw.scalars().all()

    async def get_by_coupon_code_transaction(
        self, code: str, transaction_id: str
    ):
        """
        Get a model by coupon_id.

        :param code: code of model.
        :param transaction_id: transaction_id of usage history model.
        return: tuple of streams of model
        """
        raw = await self.session.execute(
            select(self.model)
            .join(UsageHistory.coupon)
            .where(self.model.transaction_id == transaction_id)
            .where(Coupon.code == code)
        )

        return raw.scalar_one()
