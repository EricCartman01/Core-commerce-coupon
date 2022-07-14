from datetime import datetime

from sqlalchemy import and_, asc, desc, func, select, update
from sqlalchemy.exc import IntegrityError, NoResultFound
from sqlalchemy.ext.asyncio import AsyncScalarResult, AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.sql.elements import BinaryExpression

from app.api.helpers.exception import IntegrityException as IntegrityException
from app.db.base import Base


class BaseRepository:
    """Class for accessing model table."""

    def __init__(self, session: AsyncSession, model: Base):
        self.session = session
        self.model = model

    async def create(self, base_model: Base):
        try:
            self.session.add(base_model)
            await self.session.flush()
            await self.session.refresh(base_model)
            return base_model
        except IntegrityError:
            await self.session.rollback()
            raise IntegrityException(f"{self.model.__name__} integrity error")

    async def get_all(
        self,
        query_filter: BinaryExpression = None,
        page: int = 1,
        size: int = 50,
    ) -> AsyncScalarResult:
        """
        #TODO: this method is coupon specific,
         it must be moved to the coupon repository

        Get all models with limit/offset pagination.

        :param query_filter: to filter list os models.

        :return: tuple of streams of model.
        """
        valid_cupom = (
            select(self.model)
            .options(selectinload(self.model.usage_histories))
            .where(
                and_(
                    self.model.valid_until >= datetime.today(),
                    self.model.delete_at.is_(None),
                    query_filter,
                ),
            )
            .order_by(asc(self.model.valid_until))
        )

        unvalid_cupom = (
            select(self.model)
            .options(selectinload(self.model.usage_histories))
            .where(
                and_(
                    self.model.valid_until < datetime.today(),
                    self.model.delete_at.is_(None),
                    query_filter,
                ),
            )
            .order_by(desc(self.model.valid_until))
        )

        if page and size:
            valid_cupom = valid_cupom.limit(size).offset((page * size) - size)
            unvalid_cupom = unvalid_cupom.limit(size).offset(
                (page * size) - size,
            )

        valid_stream = await self.session.stream(valid_cupom)
        unvalid_stream = await self.session.stream(unvalid_cupom)

        return valid_stream.scalars(), unvalid_stream.scalars()

    async def get_total(self):
        result = await self.session.execute(
            select(func.count(self.model.coupon_id)),
        )
        return result.scalar_one_or_none()

    async def get_by_id(self, model_id: int) -> Base:
        """
        Get a model by id.

        :param model_id: id of model.

        :return: a model.
        """
        raw = await self.session.execute(
            select(self.model).where(self.model.coupon_id == model_id),
        )
        return raw.scalar_one()

    async def update(
        self,
        query_filter: BinaryExpression,
        data_to_update: dict,
        force_multiples_update: bool = False,
    ) -> int:
        """
        Update a model model by criteria.

        :param query_filter: criteria of model to update.
        :param data_to_update: dict with new data to update a model.
        :param force_multiples_update: if set True, allow multiples updates.

        :returns: count of rows to updated or -1 if error.

        :raises NoResultFound: 404 - Coupon not found
        :raises AssertionError: 404 - Coupon not found
        """
        raw = await self.session.execute(
            update(self.model).where(query_filter).values(data_to_update),
        )
        if raw.rowcount == 0:
            raise NoResultFound(f"{self.model.__name__} not found")
        if not force_multiples_update and raw.rowcount > 1:
            await self.session.rollback()
            raise AssertionError("More than one row is being changed")
        return raw.rowcount
