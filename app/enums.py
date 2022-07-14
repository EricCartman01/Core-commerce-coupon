import os
from enum import Enum


class CouponType(str, Enum):
    """Coupon type enum."""

    PERCENT = "percent"
    NOMINAL = "nominal"


class UsageHistoryStatus(str, Enum):
    """Coupon Usage History status enum."""

    RESERVED = "reserved"
    CONFIRMED = "confirmed"

    @classmethod
    def choices(cls):
        return [c.value for c in cls]


class TaskStatus(str, Enum):
    """Task status enum."""

    CREATED = "created"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"

    @classmethod
    def choices(cls):
        return [c.value for c in cls]


class Environment(str, Enum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"

    def __str__(self) -> str:
        return str.__str__(self)

    @classmethod
    def is_valid(cls) -> bool:
        return os.environ.get("DD_ENV") in list(cls)
