from copy import deepcopy
from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional

import pytz
from fastapi import File, Form, UploadFile
from pydantic import BaseModel, Field
from pydantic.class_validators import root_validator, validator

from app.api.coupon.validators import (
    code_check,
    max_amount_check,
    min_purchase_amount_check,
    purchase_amount_with_discount_check,
    utc_to_localtime,
    valid_from_check,
    valid_until_check,
    value_check,
)
from app.enums import CouponType
from app.settings import Settings, settings

utc = pytz.utc
local_timezone = settings.timezone


class MessageError(BaseModel):
    error_code: str
    error_message: str


class CouponSchema(BaseModel):
    coupon_id: Optional[str]
    description: Optional[str] = None
    code: Optional[str] = None
    customer_key: Optional[str] = None
    valid_from: Optional[datetime] = None
    valid_until: Optional[datetime] = None
    max_usage: Optional[int] = None
    type: Optional[str] = None
    value: Decimal = None
    max_amount: Optional[Decimal] = None
    min_purchase_amount: Optional[Decimal] = None
    first_purchase: Optional[bool] = None
    limit_per_customer: Optional[int] = None
    active: Optional[bool] = None
    budget: Optional[Decimal] = None
    user_create: Optional[str] = None
    confirmed_usage: int = 0
    reserved_usage: int = 0
    total_usage: int = 0

    class Config:
        orm_mode = True

    _value_check = validator("value", allow_reuse=True)(value_check)
    _max_amount_check = validator("max_amount", allow_reuse=True)(
        max_amount_check,
    )
    _min_purchase_amount_check = validator(
        "min_purchase_amount",
        allow_reuse=True,
    )(min_purchase_amount_check)
    _valid_from_check = validator("valid_from", allow_reuse=True)(
        utc_to_localtime,
    )
    _valid_until_check = validator("valid_until", allow_reuse=True)(
        utc_to_localtime,
    )


class CouponSchemaBase(BaseModel):
    description: Optional[str] = None
    code: str
    customer_key: Optional[str] = None
    valid_from: datetime
    valid_until: datetime
    max_usage: int = Field(None, gt=0)
    type: CouponType
    value: Decimal = Field(..., gt=0)
    max_amount: Optional[Decimal] = Field(None, gt=0)
    min_purchase_amount: Optional[Decimal] = Field(None, gt=0)
    first_purchase: Optional[bool] = False
    limit_per_customer: Optional[int] = Field(None, gt=0)
    budget: Optional[Decimal] = Field(None, ge=0)
    user_create: str

    _code_check = validator("code", allow_reuse=True)(code_check)
    _valid_from_check = validator("valid_from", allow_reuse=True)(
        valid_from_check,
    )
    _valid_until_check = validator("valid_until", allow_reuse=True)(
        valid_until_check,
    )

    @root_validator
    def check_if_valid_until_is_greater_than_valid_from(cls, values):
        valid_from, valid_until = values.get("valid_from"), values.get(
            "valid_until",
        )
        if (
            valid_from
            and valid_until
            and valid_from.replace(tzinfo=None)
            > valid_until.replace(tzinfo=None)
        ):
            raise ValueError("valid_until must be greater than valid_from")
        return values

    @root_validator
    def check_not_bigger_than_100_with_percent(cls, values):
        coupon_value, coupon_type = values.get("value"), values.get("type")
        if coupon_type is CouponType.PERCENT and coupon_value > 100:
            raise ValueError(
                "Value must not be bigger than 100 when type is percent.",
            )
        return values

    @root_validator
    def checks_if_coupon_type_nominal_and_exists_max_amount(cls, values):
        max_amount, coupon_type = values.get("max_amount"), values.get("type")
        if coupon_type is CouponType.NOMINAL and max_amount:
            raise ValueError(
                "Nominal type coupons don't allow max_amount attribute.",
            )
        return values


class CouponInputSchema(CouponSchemaBase):
    """DTO for creating new store model."""

    @root_validator
    def check_is_not_past_day(cls, values):
        valid_from, valid_until = values.get("valid_from"), values.get(
            "valid_until",
        )
        today = date.today()
        if (
            valid_from
            and valid_until
            and (valid_from.date() < today or valid_until.date() < today)
        ):
            raise ValueError(
                "valid_from and valid_until must be greater than today",
            )
        return values


class CouponUpdateSchema(CouponSchemaBase):
    """DTO for updating store model."""

    @root_validator
    def check_if_valid_until_is_not_past_day(cls, values):
        valid_from, valid_until = values.get("valid_from"), values.get(
            "valid_until",
        )
        today = date.today()
        if valid_from and valid_until and valid_until.date() < today:
            raise ValueError("valid_until must be greater than today")
        return values


class CouponValidateSchema(BaseModel):
    description: Optional[str] = None
    code: Optional[str] = None
    type: Optional[str] = None
    value: Decimal = None
    purchase_amount_with_discount: Optional[Decimal] = None

    class Config:
        orm_mode = True

    _value_check = validator("value", allow_reuse=True)(value_check)
    _purchase_amount_with_discount_check = validator(
        "purchase_amount_with_discount",
        allow_reuse=True,
    )(purchase_amount_with_discount_check)


class CouponReservedInputSchema(BaseModel):
    transaction_id: str
    customer_key: str
    purchase_amount: Decimal
    first_purchase: bool


class CouponUnreservedConfirmedInputSchema(BaseModel):
    transaction_id: str


class CouponInputWithManyCustomers(CouponSchemaBase):
    customer_keys: Optional[List[str]] = None
    file_with_customer_keys: Optional[UploadFile] = None

    @root_validator
    def check_customer_keys_single_str_list(cls, values):
        customer_keys = values.get("customer_keys")
        if customer_keys is not None:
            if len(customer_keys) == 1:
                customer_keys = customer_keys[0].split(",")
            values["customer_keys"] = [
                key for key in customer_keys if key.strip() != ""
            ]

        return values

    @root_validator
    def check_file_is_csv(cls, values):
        file: UploadFile = values.get("file_with_customer_keys")

        if (file is not None) and (file.content_type.find("csv") == -1):
            raise ValueError("file must be in CSV format")

        return values

    def get_coupon_schema(self, customer_key: str) -> CouponInputSchema:
        copy_data = deepcopy(
            self.dict(exclude={"file_with_customer_keys"}),
        )
        del copy_data["customer_keys"]
        copy_data["customer_key"] = customer_key
        return CouponInputSchema(**copy_data)

    def get_data_as_dict(self):
        copy_data = deepcopy(
            self.dict(exclude={"file_with_customer_keys"}),
        )

        copy_data["valid_from"] = copy_data["valid_from"].isoformat()
        copy_data["valid_until"] = copy_data["valid_until"].isoformat()
        copy_data["value"] = str(copy_data["value"])
        copy_data["max_amount"] = str(copy_data["max_amount"])
        copy_data["min_purchase_amount"] = str(
            copy_data["min_purchase_amount"],
        )
        copy_data["budget"] = str(copy_data["budget"])
        return copy_data

    @classmethod
    def as_form(
        cls,
        description: str = Form(None),
        code: str = Form(...),
        valid_from: datetime = Form(...),
        valid_until: datetime = Form(...),
        max_usage: int = Form(None, gt=0),
        type: CouponType = Form(...),
        value: Decimal = Form(..., gt=0),
        max_amount: Optional[Decimal] = Form(None, gt=0),
        min_purchase_amount: Optional[Decimal] = Form(None, gt=0),
        first_purchase: Optional[bool] = Form(False),
        limit_per_customer: Optional[int] = Form(None, gt=0),
        budget: Optional[Decimal] = Form(None, ge=0),
        user_create: str = Form(""),
        customer_keys: Optional[List[str]] = Form(None),
        file_with_customer_keys: Optional[UploadFile] = File(None),
    ):
        return cls(
            description=description,
            code=code,
            valid_from=valid_from,
            valid_until=valid_until,
            max_usage=max_usage,
            type=type,
            value=value,
            max_amount=max_amount,
            min_purchase_amount=min_purchase_amount,
            first_purchase=first_purchase,
            limit_per_customer=limit_per_customer,
            budget=budget,
            user_create=user_create,
            customer_keys=customer_keys,
            file_with_customer_keys=file_with_customer_keys,
        )
