from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import relationship

from app.db.base import Base, CreateCustomID, CustomID
from app.enums import UsageHistoryStatus

STRING_SIZE = 200
STRING_SIZE_LESS = 60


class Coupon(Base):
    """Model of coupon."""

    __tablename__ = "coupon"
    coupon_id = Column(
        CustomID(),
        primary_key=True,
        default=CreateCustomID(),
        server_default=CreateCustomID(),
    )
    description = Column(String(length=STRING_SIZE))
    code = Column(String(STRING_SIZE_LESS), nullable=False)
    customer_key = Column(String(STRING_SIZE))
    valid_from = Column(DateTime(timezone=True))
    valid_until = Column(DateTime(timezone=True))
    max_usage = Column(Integer)
    type = Column(String(STRING_SIZE_LESS), nullable=False)
    value = Column(Numeric(scale=2), nullable=False)
    max_amount = Column(Numeric(scale=2))
    min_purchase_amount = Column(Numeric(scale=2))
    first_purchase = Column(Boolean, nullable=False, default=False)
    active = Column(Boolean, nullable=False, default=True)
    budget = Column(Numeric(scale=2))
    create_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=func.now(),
    )
    user_create = Column(String(STRING_SIZE))
    limit_per_customer = Column(Integer)
    delete_at = Column(DateTime(timezone=True))
    user_delete = Column(String(STRING_SIZE))
    usage_histories = relationship("UsageHistory", backref="coupon")

    @property
    def accumulated_value(self):
        return sum(
            usage_history.discount_amount
            for usage_history in self.usage_histories
        )

    @property
    def confirmed_usage(self):
        confirmed_histories = [
            h for h in self.usage_histories if h.is_confirmed()
        ]

        return len(confirmed_histories)

    @property
    def reserved_usage(self):
        reserved_histories = [
            h for h in self.usage_histories if h.is_reserved()
        ]

        return len(reserved_histories)

    @property
    def total_usage(self):
        return self.confirmed_usage + self.reserved_usage


Index(
    "coupon_duplicate_index",
    Coupon.code,
    Coupon.customer_key,
    Coupon.valid_from,
    Coupon.valid_until,
)


class UsageHistory(Base):
    """Model of Coupon Usage History."""

    __tablename__ = "usage_history"
    id = Column(
        CustomID(),
        primary_key=True,
        default=CreateCustomID(),
        server_default=CreateCustomID(),
    )
    transaction_id = Column(String(STRING_SIZE), nullable=False)
    customer_key = Column(String(STRING_SIZE), nullable=False)
    discount_amount = Column(Numeric(scale=2), nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=func.now(),
    )
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    status = Column(
        Enum(*UsageHistoryStatus.choices(), name="usagehistorystatus"),
        nullable=False,
        default=UsageHistoryStatus.RESERVED.value,
    )
    coupon_id = Column(
        CustomID(),
        ForeignKey("coupon.coupon_id"),
        nullable=False,
    )
    __table_args__ = (
        UniqueConstraint(
            "transaction_id",
            "coupon_id",
            name="usage_history_transaction_id_coupon_id_key",
        ),
    )

    def is_confirmed(self):
        return self.status == UsageHistoryStatus.CONFIRMED

    def is_reserved(self):
        return self.status == UsageHistoryStatus.RESERVED
