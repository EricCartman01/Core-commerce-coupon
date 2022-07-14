from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.coupon.v1.schema import CouponReservedInputSchema
from app.models.coupon import Coupon, UsageHistory
from app.repository.usage_history import UsageHistoryRepository
from app.services.utils.calculate_discount import calculate_discount


class UsageHistoryService:
    """Class for accessing model table."""

    def __init__(
        self,
        db_session: AsyncSession,
    ):
        self.usage_history_repository = UsageHistoryRepository(db_session)

    async def create(
        self, coupon: Coupon, coupon_reserved_input: CouponReservedInputSchema
    ):
        """Create a UsageHistory model
        :param coupon: Coupon model
        :param coupon_reserved_input: Input schema

        return: new UsageHistory model.
        """

        discount_amount = calculate_discount(
            coupon_reserved_input.purchase_amount,
            coupon.type,
            coupon.value,
            coupon.max_amount,
        )

        usage_history = UsageHistory(
            transaction_id=coupon_reserved_input.transaction_id,
            customer_key=coupon_reserved_input.customer_key,
            discount_amount=discount_amount,
            coupon_id=coupon.coupon_id,
        )

        usage_history_model = await self.usage_history_repository.create(
            usage_history
        )

        return usage_history_model
