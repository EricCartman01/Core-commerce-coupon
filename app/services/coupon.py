import json
from datetime import datetime, timezone
from decimal import Decimal

from fastapi import BackgroundTasks
from loguru import logger
from sqlalchemy import and_
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.status import (
    HTTP_404_NOT_FOUND,
    HTTP_409_CONFLICT,
    HTTP_412_PRECONDITION_FAILED,
)

from app.api.coupon.v1.schema import (
    CouponInputWithManyCustomers,
    CouponReservedInputSchema,
    CouponSchema,
)
from app.api.helpers.exception import (
    CouponAlreadyConfirmed,
    ExceedBudgetLimitException,
    HTTPError,
    LimitPerCustomerException,
    MaxUsageException,
    TransactionIdException,
)
from app.enums import UsageHistoryStatus
from app.models.coupon import Coupon, UsageHistory
from app.models.task import Task
from app.repository.coupon import CouponRepository
from app.repository.task import TaskRepository
from app.repository.usage_history import UsageHistoryRepository
from app.services.storage import StorageAWSService
from app.services.usage_history import UsageHistoryService
from app.services.utils.calculate_discount import calculate_discount
from app.services.utils.task_manager import task_wrapper


class CouponService:
    """Class for accessing model table."""

    def __init__(
        self,
        db_session: AsyncSession,
    ):
        self.coupon_repository = CouponRepository(db_session)
        self.usage_history_repository = UsageHistoryRepository(db_session)
        self.usage_history_service = UsageHistoryService(db_session)
        self.task_repository = TaskRepository(db_session)
        self.filter_dict = {
            "active": lambda value: Coupon.active == value,
            "valid_from": lambda value: Coupon.valid_from >= value,
            "valid_until": lambda value: Coupon.valid_until <= value,
            "description": lambda value: Coupon.description == value,
            "code": lambda value: Coupon.code == value,
        }
        self.db_session = db_session

    async def update_by_id(self, coupon_id: str, updated_coupon_object: dict):
        """
        Update coupon model in database.

        :param coupon_id: new coupon model item.
        :param updated_coupon_object: new coupon model item.

        :return: new coupon model.

        :raises HTTPError: 404 - Not found.
        :raises HTTPError: 409 - Conflict.
        """
        has_duplicated_name = (
            await self.coupon_repository.check_duplicate_coupon_name(
                code=updated_coupon_object["code"],
                customer_key=updated_coupon_object["customer_key"],
                valid_from=updated_coupon_object["valid_from"],
                valid_until=updated_coupon_object["valid_until"],
                coupon_id=coupon_id,
            )
        )

        if has_duplicated_name:
            raise HTTPError(
                status_code=HTTP_409_CONFLICT,
                error_message="coupon name already been taken",
                error_code="duplicated_coupon",
            )

        coupon = await self.coupon_repository.get_by_id(coupon_id)
        usage_histories = await self.usage_history_repository.get_by_coupon_id(
            str(coupon_id),
        )

        total_coupon_usage = len(usage_histories)

        await self.check_coupon_max_usage(
            total_coupon_usage,
            updated_coupon_object["max_usage"],
        )
        await self.check_coupon_valid_from(
            coupon,
            updated_coupon_object,
            total_coupon_usage,
        )
        if total_coupon_usage > 0:
            updated_coupon_object = {
                "max_usage": updated_coupon_object["max_usage"],
                "valid_until": updated_coupon_object["valid_until"],
            }

        return await self.coupon_repository.update(
            (Coupon.coupon_id == coupon_id),
            updated_coupon_object,
        )

    async def delete_by_id(self, coupon_id: str):
        """
        Delete coupon model in database.

        :param coupon_id: new coupon model item.

        :return: new coupon model.
        """
        is_valid_delete = await self.coupon_repository.check_valid_delete(
            coupon_id=coupon_id,
        )

        if not is_valid_delete:
            raise HTTPError(
                status_code=HTTP_409_CONFLICT,
                error_message="Could not delete an used coupon",
                error_code="error_on_delete",
            )

        return await self.coupon_repository.update(
            (Coupon.coupon_id == coupon_id),
            {"active": False, "delete_at": datetime.now()},
        )

    async def add_reserved(
        self,
        code: str,
        coupon_reserved_input: CouponReservedInputSchema,
    ):
        """
        Add reserved usage to coupon model in database.

        :param code: new coupon model item.

        :return: new coupon model.

        :raises HTTPError: 400 - Bad request.
        :raises HTTPError: 409 - conflict.
        """
        upper_code = code.upper()
        coupon_model = await self.coupon_repository.get_valid_coupon(
            upper_code,
            coupon_reserved_input.customer_key,
            coupon_reserved_input.first_purchase,
            coupon_reserved_input.purchase_amount,
        )

        total_coupon_usage = len(coupon_model.usage_histories)
        add_reserve = 1

        await self.check_if_usage_history_exist(
            coupon_reserved_input.transaction_id,
            coupon_model.coupon_id,
        )

        await self.check_coupon_max_usage(
            total_coupon_usage + add_reserve,
            coupon_model.max_usage,
        )

        await self.check_limit_per_customer(
            coupon_model,
            coupon_reserved_input.customer_key,
        )

        await self.check_budget_limit(
            coupon_model,
            coupon_reserved_input.purchase_amount,
        )

        await self.usage_history_service.create(
            coupon_model,
            coupon_reserved_input,
        )

        return coupon_model

    async def remove_reserved(self, code: str, transaction_id: str):
        """
        Remove reserved usage to coupon model in database.

        :param code: new coupon model item.

        :return: new coupon model.

        :raises HTTPError: 400 - Bad request.
        """
        upper_code = code.upper()
        usage_history_model = (
            await self.usage_history_repository.get_by_coupon_code_transaction(
                code=upper_code,
                transaction_id=transaction_id,
            )
        )

        if usage_history_model.is_confirmed():
            raise CouponAlreadyConfirmed()

        await self.usage_history_repository.delete(
            transaction_id=transaction_id,
        )

        return usage_history_model

    async def add_confirmed(self, code: str, transaction_id: str):
        """
        Add confirmed usage to coupon model in database.

        :param code: new coupon model item.

        :return: new coupon model.

        :raises HTTPError: 404 - Not Found.
        """
        upper_code = code.upper()

        usage_history_model = (
            await self.usage_history_repository.get_by_coupon_code_transaction(
                code=upper_code,
                transaction_id=transaction_id,
            )
        )

        usage_history_model.status = UsageHistoryStatus.CONFIRMED

        return usage_history_model

    async def get_filter(self, filter: dict, page: int = 1, size: int = 50):
        """
        Get coupon list in database by filter.

        :param filter: new coupon model item.

        :return: paginated coupon model list.
        """
        filter_sql = [
            self.filter_dict[key](value)
            for key, value in filter.items()
            if value
        ]

        collections = await self.coupon_repository.get_all(
            query_filter=and_(True, *filter_sql),
            page=page,
            size=size,
        )
        coupons = []
        for collection in collections:
            coupons += await collection.fetchall()
        total = await self.coupon_repository.get_total()
        result = {
            "items": [
                CouponSchema.from_orm(coupon) for coupon in coupons[:size]
            ],
            "page": page,
            "size": size,
            "total": total,
        }
        return result

    async def create_coupon(self, create_coupon_object: Coupon) -> Coupon:
        """
        Create coupon model in database.

        :param create_coupon_object: new coupon model item.

        :return: new coupon model.

        :raises HTTPError: 409 - conflict.
        """
        has_duplicated_name = (
            await self.coupon_repository.check_duplicate_coupon_name(
                code=create_coupon_object.code,
                customer_key=create_coupon_object.customer_key,
                valid_from=create_coupon_object.valid_from,
                valid_until=create_coupon_object.valid_until,
            )
        )

        if has_duplicated_name:
            raise HTTPError(
                status_code=HTTP_409_CONFLICT,
                error_message="coupon name already been taken",
                error_code="duplicated_coupon",
            )

        coupon_model = Coupon(**create_coupon_object.dict())
        coupon = await self.coupon_repository.create(coupon_model)

        return await self.coupon_repository.get_by_id(coupon.coupon_id)

    async def create_coupon_model(
        self, create_coupon_object: Coupon
    ) -> Coupon:
        """
        Create coupon model in database.

        :param create_coupon_object: new coupon model item.

        :return: new coupon model.

        :raises HTTPError: 409 - conflict.
        """
        logger.info(f"oiii3")
        has_duplicated_name = (
            await self.coupon_repository.check_duplicate_coupon_name(
                code=create_coupon_object.code,
                customer_key=create_coupon_object.customer_key,
                valid_from=create_coupon_object.valid_from,
                valid_until=create_coupon_object.valid_until,
            )
        )

        if has_duplicated_name:
            raise HTTPError(
                status_code=HTTP_409_CONFLICT,
                error_message="coupon name already been taken",
                error_code="duplicated_coupon",
            )

        coupon_model = Coupon(**create_coupon_object.dict())
        return coupon_model

    async def validate_coupon(
        self,
        code,
        customer_key,
        purchase_amount,
        first_purchase,
    ) -> dict:
        """
        Create coupon model in database.

        :param code: Code of coupon.
        :param customer_key: Key of user.
        :param purchase_amount: total purchase value.
        :param first_purchase: Indicates if is first purchase.

        :return: An object with discount infos.

        """

        try:
            upper_code = code.upper()
            coupon = await self.coupon_repository.get_valid_coupon(
                upper_code,
                customer_key,
                first_purchase,
                purchase_amount,
            )

            purchase_amount_with_discount = self.calculate_total_purchase(
                purchase_amount,
                coupon.type,
                coupon.value,
                coupon.max_amount,
            )

            return {
                "code": coupon.code,
                "description": coupon.description,
                "type": coupon.type,
                "value": coupon.value,
                "purchase_amount_with_discount": purchase_amount_with_discount,
            }

        except NoResultFound:
            raise HTTPError(
                status_code=HTTP_404_NOT_FOUND,
                error_message="coupon not found",
                error_code="coupon_not_availiable",
            )

    async def activate_coupon(self, coupon_id: str):
        """
        Activate a coupon.

        :param coupon_id: A id of a coupon

        :return: new coupon model.

        :raises HTTPError: 404 - Coupon cannot be found
        :raises HTTPError: 409 - Coupon cannot be deactivate
        """
        already_active = await self.coupon_repository.activate_coupon(
            coupon_id,
        )

        if already_active:
            raise HTTPError(
                status_code=HTTP_409_CONFLICT,
                error_message="Coupon is already active.",
                error_code="coupon_already_active",
            )

    async def deactivate_coupon(self, coupon_id: str):
        """
        Deactivate a coupon.

        :param coupon_id: A id of a coupon

        :return: new coupon model.

        :raises HTTPError: 404 - Coupon cannot be found
        :raises HTTPError: 409 - Coupon cannot be deactivate
        """

        already_deactive = await self.coupon_repository.deactivate_coupon(
            coupon_id,
        )

        if already_deactive:
            raise HTTPError(
                status_code=HTTP_409_CONFLICT,
                error_message="Coupon is already deactive.",
                error_code="coupon_already_deactive",
            )

    async def check_coupon_max_usage(
        self,
        total_coupon_usage: int,
        max_usage: int,
    ):
        """
        Check if max usage was reached.

        :param total_coupon_usage: Total coupon usage.
        :param max_usage: Max use of a coupon.

        :return: None.

        :raises HTTPError: 412 - PRECONDITION_FAILED.
        """
        cant_be_updated = (
            max_usage is not None and total_coupon_usage > max_usage
        )

        if cant_be_updated:
            raise MaxUsageException()

    async def check_coupon_valid_from(
        self,
        coupon: Coupon,
        updated_coupon: dict,
        total_coupon_usage: int,
    ):
        """
        Check if valid_from is a valid date.

        :param coupon: coupon model item.
        :param updated_coupon_object: new coupon data to be updated.
        :param total_coupon_usage: total coupon usage

        :return: None.

        :raises HTTPError: 412 - PRECONDITION_FAILED.
        """
        if (
            total_coupon_usage > 0
            and updated_coupon["valid_from"].replace(tzinfo=None)
            < coupon.valid_from.replace(tzinfo=None)
        ) or (
            coupon.valid_from.replace(tzinfo=None)
            < updated_coupon["valid_from"].replace(tzinfo=None)
            < datetime.now(timezone.utc).replace(tzinfo=None)
        ):
            raise HTTPError(
                status_code=HTTP_412_PRECONDITION_FAILED,
                error_message="Attribute valid_from is invalid.",
                error_code="valid_from_invalid",
            )

    def calculate_total_purchase(
        self,
        purchase_amount: Decimal,
        discount_type: str,
        discount_value: Decimal,
        max_amount: Decimal,
    ) -> Decimal:
        """
        Calculate purchase_amout with.
        :param purchase_amount: total purchase value.
        :param discount_type: type discount (percent, nominal).
        :param discount_value: value of discount.
        :param max_amount: max value of discout.
        :return: total purchase with discount.
        """

        discount_value = calculate_discount(
            purchase_amount,
            discount_type,
            discount_value,
            max_amount,
        )

        purchase_amount_with_discount = purchase_amount - discount_value
        return max(0, purchase_amount_with_discount)

    async def check_limit_per_customer(
        self,
        coupon: Coupon,
        customer_key: str,
    ):
        usages_by_customer = await self.usage_history_repository.get_all(
            and_(
                UsageHistory.customer_key == customer_key,
                UsageHistory.coupon_id == coupon.coupon_id,
            ),
        )
        all_usages_by_customer = await usages_by_customer.fetchall()
        if coupon.limit_per_customer and not (
            len(all_usages_by_customer) < coupon.limit_per_customer
        ):
            raise LimitPerCustomerException()

    async def check_budget_limit(
        self,
        coupon: Coupon,
        purchase_amount: Decimal,
    ):
        discount_amount = calculate_discount(
            purchase_amount,
            coupon.type,
            coupon.value,
            coupon.max_amount,
        )
        accumulated_value = coupon.accumulated_value

        exceed_budget_limit = coupon.budget and coupon.budget < (
            accumulated_value + discount_amount
        )

        if exceed_budget_limit:
            raise ExceedBudgetLimitException()

    async def check_if_usage_history_exist(
        self,
        transaction_id: str,
        coupon_id: str,
    ):
        """
        Check if already exist a reserve with the transaction id.

        :param transaction_id: transaction_id of the usage history object
        :param coupon_id: coupon id

        :raises TransactionIdException.
        """
        try:
            usage_history = await self.usage_history_repository.get_one(
                coupon_id=coupon_id,
                transaction_id=transaction_id,
            )
            if usage_history:
                raise TransactionIdException()
        except NoResultFound:
            pass

    async def create_task(
        self,
        form_data: CouponInputWithManyCustomers,
        background_tasks: BackgroundTasks,
    ):
        from app.services.handlers import create_bulk_coupons_by_customers

        file_key = None
        try:
            if form_data.file_with_customer_keys:
                file_key = StorageAWSService().upload_file_obj(
                    form_data.file_with_customer_keys.file,
                )
        except Exception as e:
            logger.exception(
                f"Erro ao fazer upload do arquivo para storage: {e}",
            )

        data_dict = form_data.get_data_as_dict()
        data_dict["file_key"] = file_key

        task = Task(data=json.dumps(data_dict))

        task_model = await self.task_repository.create(task)
        await create_bulk_coupons_by_customers(form_data, self.db_session)

        # background_tasks.add_task(
        #     task_wrapper,
        #     create_bulk_coupons_by_customers,
        #     task_model.id,
        #     form_data,
        #     self.db_session,
        # )
        return task_model
